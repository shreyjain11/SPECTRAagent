#!/usr/bin/env python3
"""Rebuild STATE Codex-r1 input-side features from verified public source bytes.

Scientific execution is intended on exxact05. No downloads or model inference.
Two independently resumable stages: obs and expression. A cached stage requires
matching source specifications, method hashes and every recorded output hash.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

import numpy as np
import pandas as pd
import pyarrow
import pyarrow.dataset as ds
from scipy.stats import spearmanr

CELLS = ['C32', 'HOP62', 'HepG2/C3A', 'Hs 766T', 'PANC-1']
OBS = 'acquisition/tahoe_obs_metadata.parquet'
EXPRESSION = ['acquisition/DepMap_Model_23Q4.csv',
              'acquisition/OmicsExpressionProteinCodingGenesTPMLogp1_23Q4.csv',
              'acquisition/cmp_rnaseq_all_20220624.zip',
              'acquisition/state_tahoe_cell_type_onehot_map_verified.pkl']


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8*1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def load_original(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def source_entries(root, needed):
    catalog = json.loads((root/'methods/sources.json').read_text())['inputs']
    lookup = {row['path']:row for row in catalog}
    return [{key:lookup[name][key] for key in ['path','bytes','sha256','url']} for name in needed]


def method_hashes(root):
    paths = ['methods/build_features.py','methods/original/01_build_prospective_axis.py',
             'methods/original/04_analyze_frozen_axis.py']
    return {p:digest(root/p) for p in paths}


def cache_valid(receipt_path, output, sources, methods):
    if not receipt_path.is_file():
        return False
    try:
        r = json.loads(receipt_path.read_text())
        if not r.get('completed') or r.get('source_specifications') != sources or r.get('method_sha256') != methods:
            return False
        outputs = r.get('outputs', [])
        if not outputs:
            return False
        return all((output/x['path']).is_file() and (output/x['path']).stat().st_size==x['bytes'] and digest(output/x['path'])==x['sha256'] for x in outputs)
    except (OSError, ValueError, KeyError):
        return False


def verify_sources(inputs, entries):
    verified=[]
    for row in entries:
        p=inputs/row['path']
        if not p.is_file():
            raise FileNotFoundError(f"Required original input missing: {p}. Complete the verified source download before this stage.")
        if p.stat().st_size != row['bytes']:
            raise ValueError(f"Incomplete or unexpected input size: {p}")
        print(f"Hashing original input: {row['path']}", flush=True)
        actual=digest(p)
        if actual != row['sha256']:
            raise ValueError(f"Original input SHA-256 mismatch: {p}")
        verified.append({**row,'actual_sha256':actual,'verified':True})
    return verified


def expected_table(root, relative):
    for base in [root/'summary_replay/inputs/supporting/results', root/'recovery/original_handoff/supporting/results']:
        p=base/relative
        if p.is_file() and p.stat().st_size:
            return pd.read_csv(p), {'path':str(p.relative_to(root)), 'sha256':digest(p)}
    return None,None


def compare_values(actual, original, cols, atol=1e-10):
    a=actual.set_index('cell_line'); b=original.set_index('cell_line')
    assert set(a.index)==set(b.index), 'Held-out context identity mismatch'
    errors={}
    for left,right in cols:
        x=a.loc[b.index,left].to_numpy(float); y=b[right].to_numpy(float)
        np.testing.assert_allclose(x,y,rtol=0,atol=atol)
        errors[left]=float(np.max(np.abs(x-y)))
    return errors


def build_obs(root, inputs, out):
    obs=inputs/OBS
    dataset=ds.dataset(obs,format='parquet')
    fields=['cell_name','drug','drugname_drugconc','pass_filter','plate','gene_count',
            'tscp_count','pcnt_mito','S_score','G2M_score','phase']
    missing=sorted(set(fields)-set(dataset.schema.names))
    if missing:
        raise ValueError(f"Original metadata fields unavailable: {missing}")
    print('Extracting original DMSO_TF cells with column projection',flush=True)
    selected=ds.field('cell_name').isin(CELLS)&(ds.field('drug')=='DMSO_TF')
    columns=['cell_name','plate','pass_filter','gene_count','tscp_count','pcnt_mito','S_score','G2M_score','phase']
    t=dataset.to_table(columns=columns,filter=selected).to_pandas()
    assert set(t.cell_name.astype(str))==set(CELLS)
    grouped=t.groupby('cell_name',observed=True)
    hetero=grouped.agg(n_control=('gene_count','size'),gene_mean=('gene_count','mean'),
        gene_sd=('gene_count','std'),tscp_mean=('tscp_count','mean'),tscp_sd=('tscp_count','std'),
        mito_mean=('pcnt_mito','mean'),mito_sd=('pcnt_mito','std'),S_sd=('S_score','std'),G2M_sd=('G2M_score','std'))
    phase_counts=t.groupby(['cell_name','phase'],observed=True).size()
    probabilities=phase_counts/phase_counts.groupby(level=0,observed=True).transform('sum')
    entropy=-(probabilities*np.log(probabilities)).groupby(level=0,observed=True).sum()
    hetero['phase_entropy']=entropy
    hetero=hetero.rename_axis('cell_line').reset_index()
    hetero.to_csv(out/'baseline_heterogeneity.csv',index=False)
    sphase=hetero[['cell_line','n_control','S_sd']].copy()
    sphase['axis_value']=sphase.S_sd
    sphase['axis_level']=sphase.axis_value.rank(method='first').astype(int)
    sphase=sphase.sort_values('axis_value')
    sphase.to_csv(out/'s_phase_features.csv',index=False)
    # Native event 922: first integer in plate label; sample SD by odd/even/all.
    t['plate_num']=t.plate.astype(str).str.extract(r'(\d+)')[0].astype(int)
    plates=[]
    for subset,mask in [('odd',t.plate_num%2==1),('even',t.plate_num%2==0),('all',t.plate_num>0)]:
        part=t[mask].groupby('cell_name',observed=True).S_score.agg(['std','count']).reset_index()
        part['subset']=subset;plates.append(part)
    plate=pd.concat(plates,ignore_index=True)
    plate.to_csv(out/'s_score_axis_plate_replication.csv',index=False)
    full=t[t.pass_filter.astype(str).str.lower().eq('full')].groupby('cell_name',observed=True).S_score.agg(['std','count']).rename_axis('cell_line').reset_index()
    qc=sphase[['cell_line','S_sd','n_control']].merge(full,on='cell_line',validate='one_to_one')
    qc=qc.rename(columns={'S_sd':'recomputed_all_cell_SD','std':'full_pass_filter_SD','count':'n_full_filter'})
    old,old_prov=expected_table(root,'st_se_confirmation/spc_table.csv')
    checks={'baseline_cells':len(t),'context_count':len(sphase),'original_measurement_sources':['recovery/native_events/original-command-911.txt','recovery/native_events/original-command-922.txt'],
            'categorical_grouping':'observed=True removes unused categories; entropy includes only positive-frequency observed phases'}
    if old is not None:
        checks['sphase_vs_original_max_abs_error']=compare_values(sphase,old,[('axis_value','axis_value')],1e-12)
        checks['sphase_original_comparison_source']=old_prov
        qc=qc.merge(old[['cell_line','axis_value']].rename(columns={'axis_value':'frozen_all_cell_SD'}),on='cell_line',validate='one_to_one')
        qc['all_cell_exact_1e12']=(qc.recomputed_all_cell_SD-qc.frozen_all_cell_SD).abs()<1e-12
    qc.to_csv(out/'s_phase_qc_filter_sensitivity.csv',index=False)
    old_qc,qc_prov=expected_table(root,'distance_closure_validation/s_phase_qc_filter_sensitivity.csv')
    if old_qc is not None:
        checks['qc_vs_original_max_abs_error']=compare_values(qc,old_qc,[('recomputed_all_cell_SD','recomputed_all_cell_SD'),('full_pass_filter_SD','full_pass_filter_SD')],1e-12)
        checks['qc_original_comparison_source']=qc_prov
    pivot=plate.pivot(index='cell_name',columns='subset',values='std')
    checks['odd_even_rank_spearman']=float(spearmanr(pivot.odd,pivot.even).statistic)
    checks['full_filter_rank_spearman']=float(spearmanr(qc.recomputed_all_cell_SD,qc.full_pass_filter_SD).statistic)
    checks['n_control_by_context']=dict(zip(hetero.cell_line,hetero.n_control.astype(int)))
    print('Computing per-condition cell counts with unchanged original projected scanner',flush=True)
    original=load_original(root/'methods/original/04_analyze_frozen_axis.py','state_original_count_method')
    with tempfile.TemporaryDirectory(prefix='count-stage-',dir=out) as temp:
        counts=original.extract_cell_counts(obs,Path(temp)/'cell_counts.csv')
    assert not counts.duplicated(['cell_line','target']).any()
    assert (counts.n_cells_full<=counts.n_cells_all).all()
    counts.to_csv(out/'cell_counts.csv',index=False)
    checks['condition_count_rows']=len(counts)
    checks['condition_all_cell_total']=int(counts.n_cells_all.sum())
    checks['condition_full_cell_total']=int(counts.n_cells_full.sum())
    checks['count_method']='Unmodified 04_analyze_frozen_axis.extract_cell_counts: three projected columns, held-out context filter, batches of 500000, exact counters'
    checks['all_original_feature_comparisons_passed']=True
    files=['baseline_heterogeneity.csv','s_phase_features.csv','s_score_axis_plate_replication.csv','s_phase_qc_filter_sensitivity.csv','cell_counts.csv']
    return files,checks


def build_expression(root, inputs, out):
    archive=inputs/'acquisition/cmp_rnaseq_all_20220624.zip'
    original=root/'methods/original/01_build_prospective_axis.py'
    # This exact archive member was used in native command 377, then command 521.
    member='rnaseq_tpm_20220624.csv'
    with tempfile.TemporaryDirectory(prefix='cmp-stage-',dir=out) as temp:
        extracted=Path(temp)/member
        with zipfile.ZipFile(archive) as z:
            if member not in z.namelist():
                raise ValueError(f'Original CMP member missing: {member}')
            with z.open(member) as src,extracted.open('wb') as dst:
                shutil.copyfileobj(src,dst,8*1024*1024)
        extracted_meta={'member':member,'bytes':extracted.stat().st_size,'sha256':digest(extracted)}
        cmd=[sys.executable,str(original),'--cell-map',str(inputs/EXPRESSION[3]),
             '--sample-info',str(inputs/EXPRESSION[0]),'--ccle-expression',str(inputs/EXPRESSION[1]),
             '--cmp-expression',str(extracted),'--output-dir',str(out),'--n-genes','2000','--k-neighbors','5']
        print('Running unchanged original CMP/CCLE feature builder',flush=True)
        result=subprocess.run(cmd,text=True,capture_output=True)
        (out/'original_axis_stdout.txt').write_text(result.stdout)
        (out/'original_axis_stderr.txt').write_text(result.stderr)
        if result.returncode:
            raise RuntimeError(f'Original axis builder failed ({result.returncode}): {result.stderr[-6000:]}')
        print(result.stdout,flush=True)
    mapping=pd.read_csv(out/'cell_line_mapping.csv')
    train=mapping[(~mapping.held_out)&mapping.depmap_id.notna()]
    held=mapping[mapping.held_out].copy()
    lineage_counts=train.groupby('lineage',dropna=False).size()
    held['n_training_contexts']=held.lineage.map(lineage_counts).fillna(0).astype(int)
    held['axis_value']=-np.log1p(held.n_training_contexts)
    held['axis_level']=held.axis_value.rank(method='dense').astype(int)
    lineage=held[['cell_line','lineage','n_training_contexts','axis_value','axis_level']].sort_values(['axis_value','cell_line'])
    lineage.to_csv(out/'lineage_features.csv',index=False)
    primary=pd.read_csv(out/'primary_cmp_distances.csv')
    independent=pd.read_csv(out/'independent_ccle_distances.csv')
    checks={'cmp_extracted_member':extracted_meta,'lineage_rule':'Count mapped non-held-out training contexts by DepMap Oncotree lineage; -log1p(count), tied values retain same dense level',
            'training_mapped_contexts':len(train),'all_original_feature_comparisons_passed':True}
    old,prov=expected_table(root,'spc_table.csv')
    if old is not None:
        checks['primary_vs_original_max_abs_error']=compare_values(primary,old,[('distance','distance')],1e-10)
        checks['ccle_vs_original_max_abs_error']=compare_values(independent,old,[('distance','ccle_distance')],1e-10)
        checks['distance_original_comparison_source']=prov
    old_lineage,lp=expected_table(root,'lineage_followup/spc_table.csv')
    if old_lineage is not None:
        checks['lineage_vs_original_max_abs_error']=compare_values(lineage,old_lineage,[('axis_value','axis_value')],1e-12)
        checks['lineage_original_comparison_source']=lp
    files=['cell_line_mapping.csv','primary_cmp_distances.csv','primary_cmp_pairwise_distances.csv','primary_gene_set.txt',
           'independent_ccle_distances.csv','independent_ccle_pairwise_distances.csv','axis_replication_summary.json',
           'lineage_features.csv','original_axis_stdout.txt','original_axis_stderr.txt']
    return files,checks


def run_stage(root, inputs, out, stage, force=False):
    sources=source_entries(root,[OBS] if stage=='obs' else EXPRESSION)
    methods=method_hashes(root)
    receipt_path=out/(stage+'_receipt.json')
    if not force and cache_valid(receipt_path,out,sources,methods):
        print(json.dumps({'stage':stage,'status':'reused_verified_feature_outputs',
                          'receipt':str(receipt_path),'raw_input_presence':{x['path']:(inputs/x['path']).is_file() for x in sources},
                          'note':'Source hashes were verified at recorded computation; output/source-spec/method hashes verified now.'}),flush=True)
        return json.loads(receipt_path.read_text())
    started=time.time()
    verified=verify_sources(inputs,sources)
    files,checks=(build_obs(root,inputs,out) if stage=='obs' else build_expression(root,inputs,out))
    outputs=[{'path':name,'bytes':(out/name).stat().st_size,'sha256':digest(out/name)} for name in files]
    receipt={'schema_version':1,'stage':stage,'completed':True,'scientific_execution':'recomputed_from_verified_public_source_bytes',
             'source_specifications':sources,'verified_inputs':verified,'method_sha256':methods,
             'output_path_base':'feature_directory','outputs':outputs,'checks':checks,
             'runtime':{'python':sys.version,'numpy':np.__version__,'pandas':pd.__version__,'pyarrow':pyarrow.__version__},
             'elapsed_seconds':round(time.time()-started,3),'executed_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    write_json(receipt_path,receipt)
    print(json.dumps({'stage':stage,'status':'computed_and_verified','receipt':str(receipt_path),'checks':checks}),flush=True)
    return receipt


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--inputs',type=Path)
    parser.add_argument('--output','--features',dest='output',type=Path)
    parser.add_argument('--stage',choices=['all','obs','expression','metadata','atlas'],default='all')
    parser.add_argument('--force',action='store_true')
    args=parser.parse_args();root=args.root.resolve()
    inputs=(args.inputs or root/'inputs').resolve();out=(args.output or root/'computed/features').resolve()
    out.mkdir(parents=True,exist_ok=True)
    stage={'metadata':'obs','atlas':'expression'}.get(args.stage,args.stage)
    stages=['obs','expression'] if stage=='all' else [stage]
    for stage in stages:
        run_stage(root,inputs,out,stage,args.force)
    # This small index never asserts unfinished stages are complete.
    receipts={}
    for stage in ['obs','expression']:
        p=out/(stage+'_receipt.json')
        if p.is_file():
            r=json.loads(p.read_text())
            if cache_valid(p,out,source_entries(root,[OBS] if stage=='obs' else EXPRESSION),method_hashes(root)):
                receipts[stage]={'path':p.name,'sha256':digest(p),'completed':True}
    write_json(out/'FEATURE_RECEIPTS.json',{'schema_version':1,'receipts':receipts,'all_stages_completed':set(receipts)=={'obs','expression'}})


if __name__=='__main__':
    main()
