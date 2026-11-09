"""Portable acquisition/reconstruction recipe, authored 2026-11-08.
Original programs stay unchanged in original_runs/. This adapter fixes local paths,
freezes cohort IDs, verifies original bytes and separates data downloads from inference.
"""
from pathlib import Path
import csv, hashlib, importlib.util, json, os, shutil, subprocess, sys, urllib.request
BUNDLE = Path(__file__).resolve().parent
from bootstrap import ensure_assets
ensure_assets(BUNDLE)
MANIFEST = json.loads((BUNDLE/'ACQUISITION_MANIFEST.json').read_text())
EVIDENCE = json.loads((BUNDLE/'ORIGINAL_ACQUISITION_EVIDENCE.json').read_text())
PINS = MANIFEST['pins']
ORIGINAL_HASHES={x['remote_path']:x for x in EVIDENCE['reference_files']}

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8*1024*1024),b''):h.update(block)
    return h.hexdigest()

def _module(path):
    path=Path(path);name='acq_'+hashlib.sha256(str(path).encode()).hexdigest()[:12]
    sys.path.insert(0,str(path.parent));spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod

def panels_for(axis):return MANIFEST['axis_panels'][str(int(axis))]

def reference_item(target, workspace):
    workspace=Path(workspace).resolve();original=ORIGINAL_HASHES[target['remote_reference']]
    if target['cameo']:
        rel='experiment_structures/'+target['target_id']+'.pdb'
        url='https://huggingface.co/datasets/'+PINS['cameo_repo']+'/resolve/'+PINS['cameo_revision']+'/'+rel
        destination=workspace/'downloads/cameo'/rel
    else:
        url='https://files.rcsb.org/download/'+target['entry_id']+'.'+target['format']
        destination=workspace/'downloads/rcsb'/(target['entry_id']+'-'+original['sha256'][:16]+'.'+target['format'])
    return {'kind':'experimental_reference','target_id':target['target_id'],'url':url,'destination':str(destination),'sha256':original['sha256'],'bytes':original['bytes'],'original_remote_path':target['remote_reference'],'version_rule':'exact original SHA-256; reject changed public bytes'}

def download_plan(axis, workspace):
    items={}
    for name in panels_for(axis):
        for target in MANIFEST['panels'][name]['targets']:
            item=reference_item(target,workspace);items[item['destination']]=item
    if any(t['cameo'] for n in panels_for(axis) for t in MANIFEST['panels'][n]['targets']):
        for old in EVIDENCE['hf_download_metadata']:
            rel=old['file'];dest=str(Path(workspace).resolve()/'downloads/cameo'/rel)
            if dest in items:continue
            item={'kind':'alignment' if rel.startswith('msa/') else 'frozen_CAMEO_source','url':'https://huggingface.co/datasets/'+PINS['cameo_repo']+'/resolve/'+PINS['cameo_revision']+'/'+rel,'destination':dest,'revision':old['revision'],'version_rule':'original HF commit plus original content ETag'}
            item['sha256' if len(old['etag'])==64 else 'git_blob_sha1']=old['etag'];items[dest]=item
    return list(items.values())

def _verify(path,item):
    if item.get('sha256') and sha256(path)!=item['sha256']:raise ValueError('Original-byte SHA-256 mismatch: '+item['url'])
    if item.get('git_blob_sha1'):
        data=Path(path).read_bytes();digest=hashlib.sha1(('blob '+str(len(data))+'\0').encode()+data).hexdigest()
        if digest!=item['git_blob_sha1']:raise ValueError('Original Git blob mismatch: '+item['url'])

def download_file(item, max_bytes=2_000_000_000):
    """Download one exact source; never fall back to a different entry/format/version."""
    dest=Path(item['destination']);dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.is_file():_verify(dest,item);return {'url':item['url'],'path':str(dest),'status':'verified_cached','sha256':sha256(dest)}
    partial=dest.with_name(dest.name+'.part');total=0
    req=urllib.request.Request(item['url'],headers={'User-Agent':'SPECTRA-reproduction/1.0','Accept-Encoding':'identity'})
    try:
        with urllib.request.urlopen(req,timeout=120) as response,partial.open('wb') as out:
            while True:
                chunk=response.read(1024*1024)
                if not chunk:break
                total+=len(chunk)
                if total>max_bytes:raise ValueError('Download exceeded explicit byte limit: '+item['url'])
                out.write(chunk)
        _verify(partial,item);partial.replace(dest)
    finally:
        if partial.exists():partial.unlink()
    return {'url':item['url'],'path':str(dest),'status':'downloaded_original_bytes','sha256':sha256(dest),'bytes':total}

def fetch_references(axis,workspace):
    """Potentially large: executes only when the notebook RUN_DOWNLOADS flag is true."""
    receipts=[]
    for item in download_plan(axis,workspace):receipts.append(download_file(item))
    p=Path(workspace)/'download_receipts.json';p.write_text(json.dumps(receipts,indent=2));return receipts

def prepare_inputs(axis,workspace,require_downloads=True,reset=False):
    """Preserve archived cohort, sequences, metadata and frozen levels; replace paths only."""
    import pandas as pd
    workspace=Path(workspace).resolve();out={}
    if not reset and (workspace/'feature_reconstruction_report.json').is_file():
        import original_workflow
        return original_workflow.require_features(axis,workspace)
    for name in panels_for(axis):
        panel=MANIFEST['panels'][name];source=BUNDLE/panel['source_features']
        assert sha256(source)==panel['source_sha256']
        df=pd.read_csv(source,low_memory=False);assert df.target_id.tolist()==[t['target_id'] for t in panel['targets']]
        paths=[]
        for target,sequence in zip(panel['targets'],df.sequence):
            assert hashlib.sha256(str(sequence).encode()).hexdigest()==target['sequence_sha256']
            item=reference_item(target,workspace);path=Path(item['destination'])
            if require_downloads:
                if not path.is_file():raise FileNotFoundError('Run RUN_DOWNLOADS=True first: '+str(path))
                _verify(path,item)
            paths.append(str(path))
        df['pdb_path']=paths
        if 'msa_path' in df:df['msa_path']=[str(workspace/'downloads/cameo/msa'/(str(t)+'.a3m')) for t in df.target_id]
        dst=workspace/'panels'/name;dst.mkdir(parents=True,exist_ok=True);(dst/'model_outputs').mkdir(exist_ok=True)
        file=dst/'features.csv';df.to_csv(file,index=False)
        out[name]={'features':str(file),'results':str(dst/'target_model_results.csv'),'n_original_targets':len(df)}
    (workspace/'prepared_inputs.json').write_text(json.dumps(out,indent=2));return out

def reconstruct_features(axis,workspace):
    import original_workflow
    return original_workflow.rebuild_features(axis,workspace)


def download_model(workspace, backend='current'):
    if backend=='current':
        import current_implementation
        return current_implementation.download_original_sources(workspace)
    if backend!='legacy':raise ValueError('backend must be current or legacy')
    from huggingface_hub import snapshot_download
    dest=Path(workspace).resolve()/'models'/PINS['model_revision']
    return snapshot_download(repo_id=PINS['model_repo'],revision=PINS['model_revision'],local_dir=str(dest))

def inference_commands(axis,workspace,python=sys.executable,backend='current'):
    """Stage model-path/API adapters; original scientific inference/scoring code is preserved."""
    workspace=Path(workspace).resolve()
    import original_workflow
    prepared=original_workflow.require_features(axis,workspace);commands=[]
    if backend=='current':
        import current_implementation
        model_path=current_implementation.model_paths(workspace)['converted']
    elif backend=='legacy':model_path=workspace/'models'/PINS['model_revision']
    else:raise ValueError('backend must be current or legacy')
    for name,info in prepared.items():
        panel=MANIFEST['panels'][name];source_root=BUNDLE/panel['source_run_root'];dest=Path(info['features']).parent/'scripts';dest.mkdir(exist_ok=True)
        filename='evaluate_esmfold2_cameo.py' if name=='cameo' else 'evaluate_esmfold2_scaling_multisample.py'
        names=[filename] if name=='cameo' else ['evaluate_esmfold2_scaling.py',filename]
        changes=[]
        if backend=='current':
            shutil.copyfile(BUNDLE/'current_esmfold2_adapter.py',dest/'current_esmfold2_adapter.py')
        for fn in names:
            original=source_root/'scripts'/fn;text=original.read_text()
            new=text.replace('from_pretrained("biohub/ESMFold2", local_files_only=True)','from_pretrained('+repr(str(model_path))+', local_files_only=True)')
            if backend=='current':
                old_import='from transformers.models.esmfold2.modeling_esmfold2 import ESMFold2Model'
                if old_import not in new:raise ValueError('Expected original model import is missing: '+str(original))
                new=new.replace(old_import,'from current_esmfold2_adapter import ESMFold2Model')
            dst=dest/fn;dst.write_text(new);changes.append({'original':str(original),'original_sha256':sha256(original),'adapter':str(dst),'adapter_sha256':sha256(dst),'change':'model checkpoint path and current API/output-metadata adapter; numerical scoring and inference arguments unchanged' if backend=='current' else 'model download path only; original programs otherwise unchanged'})
        command=[str(python),str(dest/filename),'--features',info['features'],'--out',info['results']]
        for flag,value in panel['inference'].items():
            if value is not None:command+=['--'+flag.replace('_','-'),str(value)]
        commands.append({'panel':name,'backend':backend,'command':command,'cwd':str(dest.parent),'outputs':info,'changes':changes})
    (workspace/'inference_commands.json').write_text(json.dumps(commands,indent=2));return commands

def run_inference(axis,workspace,python=sys.executable,backend='current'):
    import original_workflow
    original_workflow.require_features(axis,workspace)
    feature_report=json.loads((Path(workspace)/'feature_reconstruction_report.json').read_text())
    if feature_report.get('mode')!='downloaded_raw_reconstruction':
        raise RuntimeError('Inference requires downloaded/reconstructed inputs; retained-data validation fixtures are not a fresh run.')
    if backend=='current':
        import current_implementation
        current_implementation.verify_converted_sources(workspace)
        probe='import json,platform,torch,transformers;print(json.dumps(dict(python=platform.python_version(),torch=torch.__version__,transformers=transformers.__version__,cuda=torch.version.cuda,cuda_available=torch.cuda.is_available())))'
        environment=json.loads(subprocess.check_output([str(python),'-c',probe],text=True))
        if environment['transformers']!=current_implementation.PINS['transformers'] or environment['torch'].split('+')[0]!=current_implementation.PINS['torch']:
            raise RuntimeError('Use the pinned current inference environment: '+json.dumps(environment))
        environment.update(backend=backend,source_revisions={k:current_implementation.PINS[k]['revision'] for k in ['fold','backbone']},
                           adapter_sha256=sha256(BUNDLE/'current_esmfold2_adapter.py'),
                           historical_comparison_report='IMPLEMENTATION_COMPARISON.json')
        (Path(workspace)/'current_inference_environment.json').write_text(json.dumps(environment,indent=2))
    elif not (Path(workspace)/'models'/PINS['model_revision']).is_dir():
        raise FileNotFoundError('Set RUN_MODEL_DOWNLOAD=True before RUN_INFERENCE=True.')
    for item in inference_commands(axis,workspace,python,backend):
        output=Path(item['outputs']['results']);receipt=output.with_suffix('.provenance.json')
        binding={'features_sha256':sha256(item['outputs']['features']),'backend':backend,
                 'settings':MANIFEST['panels'][item['panel']]['inference'],
                 'adapter_sha256':sha256(BUNDLE/'current_esmfold2_adapter.py'),
                 'pins_sha256':sha256(BUNDLE/'CURRENT_IMPLEMENTATION_PINS.json'),
                 'scientific_programs':{Path(change['original']).name:change['original_sha256'] for change in item['changes']}}
        if output.exists():
            if not receipt.exists() or json.loads(receipt.read_text())!=binding:
                raise RuntimeError('Existing results are not bound to these inputs/model settings. Use a new reproduction directory: '+str(output))
        else:receipt.write_text(json.dumps(binding,indent=2))
        complete=output.with_suffix('.complete.json')
        if output.exists() and complete.exists():
            checked=json.loads(complete.read_text())
            if checked.get('result_sha256')==sha256(output) and checked.get('features_sha256')==binding['features_sha256']:
                continue
        subprocess.run(item['command'],cwd=item['cwd'],check=True)
    checks=original_workflow.validate_results(axis,workspace)
    for name,check in checks.items():
        (Path(workspace)/'panels'/name/'target_model_results.complete.json').write_text(json.dumps(check,indent=2))
    return checks

def summarize_rerun(axis,workspace):
    """Run this notebook's original axis analyses, including grouped negative screens."""
    import original_workflow
    return original_workflow.run_axis(axis,workspace)
