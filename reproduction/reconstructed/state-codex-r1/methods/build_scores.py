"""Calculate condition-level log2-fold-change errors from original DE rows.

Completed caches contain newly calculated condition records, never historical
summary values. They are bound to source identities, code and output hashes.
"""
from pathlib import Path
import argparse,concurrent.futures,importlib.util,json,os,shutil,time
from fetch_sources import entries,sha256,matches

RUNS={'hvg_best':'official_scores','se_best':'official_scores_st_se','se_last':'official_scores_st_se_last'}
CONTEXTS={'C32':'C32','HOP62':'HOP62','HepG2/C3A':'HepG2-C3A','Hs 766T':'Hs 766T','PANC-1':'PANC-1'}

def dump(path,doc):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.part');tmp.write_text(json.dumps(doc,indent=2)+'\n');tmp.replace(path)

def identity(path):return {'sha256':sha256(path),'bytes':path.stat().st_size}

def build(root,workers=2,force=False):
    root=Path(root).resolve();manifest_path=root/'methods/sources.json'
    sources={e['path']:e for e in entries(json.loads(manifest_path.read_text()))}
    manifest_hash=sha256(manifest_path)
    methods={p:sha256(root/p) for p in ['methods/build_scores.py','methods/original/04_analyze_frozen_axis.py']}
    spec=importlib.util.spec_from_file_location('state_original_score_rebuild',root/'methods/original/04_analyze_frozen_axis.py')
    original=importlib.util.module_from_spec(spec);spec.loader.exec_module(original)
    def one(run,cell,stem):
        directory=root/'computed/scores'/run;receipt_path=directory/(stem+'_receipt.json')
        if not force and receipt_path.exists():
            old=json.loads(receipt_path.read_text())
            if old.get('completed') and old.get('source_manifest_sha256')==manifest_hash and old.get('method_sha256')==methods and all(matches(root/p,m) for p,m in old['outputs'].items()):
                print(json.dumps({'stage':'scores','run':run,'cell':cell,'status':'verified_computed_cache'}),flush=True);return old
        paths=[f'acquisition/official_scores/{stem}_real_de.csv',f'acquisition/{RUNS[run]}/{stem}_pred_de.csv',f'acquisition/{RUNS[run]}/{stem}_results.csv']
        inputs=[]
        for p in paths:
            entry=sources[p];actual=root/'inputs'/p
            if not matches(actual,entry):raise ValueError('Source missing or mismatched: '+p)
            inputs.append({'path':p,'sha256':entry['sha256'],'bytes':entry['bytes'],'verified':True})
        started=time.time();real,pred,result=[root/'inputs'/p for p in paths]
        table=original.compute_lfc_scores(real,pred)
        import pandas as pd
        published=pd.read_csv(result)
        if 'perturbation' not in published:raise ValueError('Original result target schema changed')
        if table.target.duplicated().any() or set(table.target)!=set(published.perturbation):raise ValueError('DE/result target identity mismatch')
        expected=1136 if cell=='PANC-1' else 1137
        if len(table)!=expected or int(table.n_genes_lfc.sum())!=expected*2000:raise ValueError('Original row-accounting check failed')
        if not (table.n_genes_lfc==2000).all():raise ValueError('Unexpected feature panel size')
        directory.mkdir(parents=True,exist_ok=True)
        output=directory/(stem+'_lfc.csv');table.to_csv(output,index=False)
        result_copy=directory/(stem+'_results.csv');shutil.copyfile(result,result_copy)
        outputs={str(p.relative_to(root)):identity(p) for p in [output,result_copy]}
        receipt={'completed':True,'reduction':'actual_original_DE_rows','run':run,'cell_line':cell,'source_manifest_sha256':manifest_hash,'method_sha256':methods,'inputs':inputs,'outputs':outputs,'targets':len(table),'DE_rows':int(table.n_genes_lfc.sum()),'elapsed_seconds':round(time.time()-started,3)}
        dump(receipt_path,receipt)
        print(json.dumps({'stage':'scores','run':run,'cell':cell,'status':'calculated_from_DE_rows','targets':len(table),'seconds':receipt['elapsed_seconds']}),flush=True)
        return receipt
    receipts=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(workers,4))) as pool:
        tasks=[pool.submit(one,run,cell,stem) for run in RUNS for cell,stem in CONTEXTS.items()]
        for task in concurrent.futures.as_completed(tasks):receipts.append(task.result())
    outputs={k:v for r in receipts for k,v in r['outputs'].items()}
    inputs={e['path']:e for r in receipts for e in r['inputs']}
    doc={'completed':True,'reduction':'actual_original_DE_rows','source_manifest_sha256':manifest_hash,'method_sha256':methods,'inputs':list(inputs.values()),'outputs':outputs,'condition_tables':len(receipts),'parts':receipts}
    dump(root/'computed/scores/score_receipt.json',doc);return doc

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1]);p.add_argument('--workers',type=int,default=2);p.add_argument('--force',action='store_true');a=p.parse_args()
    build(a.root,a.workers,a.force)

if __name__=='__main__':main()
