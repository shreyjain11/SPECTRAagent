"""Execute all five source-calculation notebooks sequentially on the chosen host."""
from pathlib import Path
import argparse,json,os,platform,shutil,subprocess,sys

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--start',type=int,default=1,choices=range(1,6));a=p.parse_args()
    root=Path(__file__).resolve().parent;logs=root/'logs';logs.mkdir(exist_ok=True);evidence=root/'execution_evidence';evidence.mkdir(exist_ok=True)
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',NUMEXPR_NUM_THREADS='1')
    for path in sorted((root/'notebooks').glob('[0-9][0-9]-state-codex-r2-*.ipynb')):
        if int(path.name[:2])<a.start:continue
        stage=json.loads(path.read_text())['metadata']['state_reconstruction']['stage']
        print(json.dumps({'event':'notebook_start','notebook':path.name,'stage':stage,'host':platform.node()}),flush=True)
        with (logs/(path.stem+'.log')).open('w') as log:
            subprocess.run([sys.executable,str(root/'execute_notebook.py'),str(path),'--cwd',str(root),'--timeout','10800'],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        receipt_path=root/'computed'/f'pipeline_{stage}_receipt.json';receipt=json.loads(receipt_path.read_text())
        if not receipt['completed'] or receipt['derived_stage_policy']!='recompute_from_source_inputs':raise ValueError('Actual source calculation was not completed')
        shutil.copy2(receipt_path,evidence/(path.stem+'_pipeline.json'))
        stage_dir=evidence/path.stem;stage_dir.mkdir(exist_ok=True)
        for record in receipt['receipts']:
            source=root/record['path'];shutil.copy2(source,stage_dir/source.name)
        print(json.dumps({'event':'notebook_completed','notebook':path.name,'stage':stage}),flush=True)
    subprocess.run([sys.executable,str(root/'notebooks/render_notebooks.py')],cwd=root,env=env,check=True)
    frozen=subprocess.run([sys.executable,'-m','pip','freeze'],text=True,capture_output=True,check=True)
    (root/'requirements-executed.txt').write_text(frozen.stdout)
    print(json.dumps({'event':'all_five_notebooks_completed','host':platform.node()}),flush=True)
if __name__=='__main__':main()
