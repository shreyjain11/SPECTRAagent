"""Execute the four notebooks sequentially, including real recalculation."""
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start',type=int,default=1,choices=range(1,5))
    parser.add_argument('--wait-for-cmp',action='store_true',help='Wait for the separately running source transfer before execution.')
    args=parser.parse_args();root=Path(__file__).resolve().parent
    logs=root/'logs';logs.mkdir(exist_ok=True)
    evidence=root/'execution_evidence';evidence.mkdir(exist_ok=True)
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    if args.wait_for_cmp:
        manifest=json.loads((root/'methods/sources.json').read_text())
        member=root/'inputs'/manifest['cmp_member']['path']
        deadline=time.monotonic()+3600
        while not member.exists():
            if time.monotonic()>deadline:raise TimeoutError('Source transfer did not complete within one hour')
            time.sleep(10)
    for path in sorted((root/'notebooks').glob('[0-9][0-9]-state-codex-r1-*.ipynb')):
        if int(path.name[:2])<args.start:continue
        print(json.dumps({'event':'notebook_start','notebook':path.name,'host':platform.node()}),flush=True)
        with (logs/(path.stem+'.log')).open('w') as stream:
            subprocess.run([sys.executable,str(root/'execute_notebook.py'),str(path),'--cwd',str(root),'--timeout','7200'],cwd=root,env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
        receipt=json.loads((root/'computed/pipeline_all_receipt.json').read_text())
        if receipt.get('derived_stage_policy')!='recompute_from_source_inputs':raise ValueError('Notebook did not recalculate derived stages')
        shutil.copy2(root/'computed/pipeline_all_receipt.json',evidence/(path.stem+'_pipeline.json'))
        shutil.copy2(root/'computed/analysis/analysis_receipt.json',evidence/(path.stem+'_analysis.json'))
        print(json.dumps({'event':'notebook_completed','notebook':path.name,'seconds':receipt['elapsed_seconds']}),flush=True)
    subprocess.run([sys.executable,str(root/'notebooks/render_notebooks.py')],cwd=root,env=env,check=True)
    frozen=subprocess.run([sys.executable,'-m','pip','freeze'],capture_output=True,text=True,check=True)
    (root/'requirements-executed.txt').write_text(frozen.stdout)
    print(json.dumps({'event':'all_notebooks_completed','host':platform.node()}),flush=True)


if __name__=='__main__':main()
