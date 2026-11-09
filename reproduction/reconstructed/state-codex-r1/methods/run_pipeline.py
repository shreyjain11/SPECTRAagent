"""Run the public-input STATE Codex r1 reconstruction on the current host.

The default path downloads original public bytes, calculates features and
condition-level errors, then refits curves and controls. Historical summary
results are used only for a separate comparison after calculation.
"""
from pathlib import Path
import argparse
import json
import os
import platform
import subprocess
import sys
import time


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--stage',choices=['all','features','scores','analysis'],default='all')
    parser.add_argument('--reuse-computed',action='store_true',
                        help='Explicitly reuse source/code/output-verified derived stages; default recalculates them.')
    args=parser.parse_args();root=args.root.resolve()
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    env.setdefault('MPLCONFIGDIR',str(root/'computed/.matplotlib'))
    started=time.time();steps=[]
    def run(script,*arguments):
        command=[sys.executable,str(root/'methods'/script),'--root',str(root),*arguments]
        print('Running '+script,flush=True)
        before=time.time();subprocess.run(command,cwd=root,env=env,check=True)
        steps.append({'script':script,'elapsed_seconds':round(time.time()-before,3)})
    if args.stage in ('all','features','scores'):
        # An existing matching file is verified, not downloaded again. The
        # manifest pins all inputs used across the four companion notebooks.
        run('download_inputs.py')
    if args.stage in ('all','features'):
        run('build_features.py','--stage','all',*([] if args.reuse_computed else ['--force']))
    if args.stage in ('all','scores'):
        run('build_scores.py',*([] if args.reuse_computed else ['--force']))
    if args.stage in ('all','analysis'):
        run('run_analysis.py',*([] if args.reuse_computed else ['--force']))
    receipt={'completed':True,'stage':args.stage,'host':platform.node(),
             'python':sys.version,'started_unix':started,
             'elapsed_seconds':round(time.time()-started,3),'steps':steps,
             'derived_stage_policy':'explicit_verified_cache_reuse' if args.reuse_computed else 'recompute_from_source_inputs'}
    destination=root/'computed'/('pipeline_'+args.stage+'_receipt.json')
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2),flush=True)


if __name__=='__main__':main()
