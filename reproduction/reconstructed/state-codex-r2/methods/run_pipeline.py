"""Run an inspectable original investigation from actual source inputs.

Notebooks pass --force by default. Without it, only validated computation
receipts may be reused, and that choice is explicit in the pipeline receipt.
"""
import argparse,json,os,platform,subprocess,sys,time
from pathlib import Path
for key in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS']:os.environ.setdefault(key,'1')
from common import dump,sha

def valid(root,name):
    p=root/'computed'/f'{name}_receipt.json'
    if not p.is_file():return False
    try:
        x=json.loads(p.read_text())
        if x.get('status')!='computed_from_public_inputs' or not x.get('outputs'):return False
        for section in ['sources','outputs']:
            for f in x[section]:
                q=root/f['path']
                if not q.is_file() or q.stat().st_size!=f['bytes'] or sha(q)!=f['sha256']:return False
        return all((root/p).exists() and sha(root/p)==h for p,h in x['methods'].items())
    except (KeyError,OSError,ValueError):return False

def run(root,stage='all',force=False):
    root=Path(root).resolve();(root/'computed').mkdir(parents=True,exist_ok=True)
    m=root/'methods/sources.json'
    if not m.exists() or any(not (root/'inputs'/x['path']).exists() for x in json.loads(m.read_text())['inputs']):
        subprocess.run([sys.executable,str(root/'methods/acquire.py'),'--root',str(root)],check=True)
    receipts=[];executed=[];reused=[]
    def step(name,fn):
        if not force and valid(root,name):reused.append(name);print('Verified calculation cache:',name,flush=True)
        else:print('Calculating from source inputs:',name,flush=True);fn();executed.append(name)
        if not valid(root,name):raise RuntimeError(f'Calculation receipt validation failed: {name}')
        receipts.append(root/'computed'/f'{name}_receipt.json')
    if stage in ['all','dose','secondary']:
        import tahoe
        step('tahoe_analysis',lambda:tahoe.run(root))
    if stage in ['all','distance','magnitude']:
        import replogle,observation_controls
        step('replogle_axis',lambda:replogle.axes(root))
        step('replogle_scores',lambda:replogle.scores(root))
        step('replogle_observations',lambda:observation_controls.run(root))
        step('replogle_analysis',lambda:replogle.analyze(root))
    if stage in ['all','magnitude','secondary','modality']:
        import tahoe,closures
        if stage in ['magnitude','modality']:
            # These are input-side calculations only; do not create an A2e/A3
            # outcome test that was never performed by the original investigator.
            tahoe.cohort(root);step('tahoe_controls',lambda:tahoe.controls(root))
        step('closures',lambda:closures.run(root))
    import plots
    plots.run(root,stage)
    result=dict(completed=True,host=platform.node(),stage=stage,derived_stage_policy='recompute_from_source_inputs' if force else 'validated_cache_or_source_recomputation',executed_stages=executed,reused_stages=reused,receipts=[dict(path=str(p.relative_to(root)),sha256=sha(p)) for p in receipts],completed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),historical_outputs_used_to_drive_calculations=False)
    dump(root/'computed'/f'pipeline_{stage}_receipt.json',result);return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--stage',choices=['all','dose','distance','magnitude','secondary','modality'],default='all');p.add_argument('--force',action='store_true');a=p.parse_args();run(a.root,a.stage,a.force)
