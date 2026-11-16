"""Execute only the declared corrected cells on hash-verified retained inputs.

Usage: OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python execute_changed_cells.py
    --repository /path/to/SPECTRAagent --work /path/to/staged/work --part kimi|opus
The staged work directory contains public-archive members under state-kimi-r1/
and state-opus-r2/. input_evidence.json records their identities and independent
pinned-score verification. This is a partial scientific reexecution, not a full
notebook execution or fresh model inference.
"""
from pathlib import Path
import argparse,json,contextlib,io,datetime,hashlib,subprocess,platform,time,sys
import numpy as np,pandas as pd,scipy,statsmodels,matplotlib
parser=argparse.ArgumentParser();parser.add_argument('--repository',type=Path,required=True);parser.add_argument('--work',type=Path,required=True);parser.add_argument('--part',choices=['kimi','opus'],required=True);args=parser.parse_args()
R=args.repository;E=R/'reproduction/corrections/scientific_20261115/state_kimi_opus'
plan=json.load(open(E/'PLAN.json'));assert hashlib.sha256((E/'PLAN.md').read_bytes()).hexdigest()==plan['plan_sha256']
def sha(data):return hashlib.sha256(data).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
driver_bytes=Path(__file__).read_bytes();(E/f'{args.part}_executed_driver.py').write_bytes(driver_bytes);total_tick=time.monotonic()
receipts=[];started=datetime.datetime.now(datetime.timezone.utc).isoformat();namespace={'WORK':args.work/('state-kimi-r1' if args.part=='kimi' else 'state-opus-r2')}

def execute(inv,test,index):
 path=R/f'reproduction/inline/state/{inv}/test-{test:02}.ipynb';nb=json.load(open(path));src=''.join(nb['cells'][index]['source']);out=io.StringIO();err=io.StringIO();ts=datetime.datetime.now(datetime.timezone.utc).isoformat();tick=time.monotonic()
 with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):exec(compile(src,str(path)+f'#cell-{index}','exec'),namespace)
 outputs=[]
 if out.getvalue():outputs.append({'name':'stdout','output_type':'stream','text':out.getvalue().splitlines(keepends=True)})
 if err.getvalue():outputs.append({'name':'stderr','output_type':'stream','text':err.getvalue().splitlines(keepends=True)})
 original=json.loads(subprocess.check_output(['git','show','1d3b45b:'+str(path.relative_to(R))],cwd=R))['cells'][index]
 record={'notebook':str(path.relative_to(R)),'cell_index':index,'source_sha256':sha(src.encode()),'baseline_source_sha256':sha(''.join(original['source']).encode()),'baseline_outputs_sha256':sha(canonical(original.get('outputs',[]))),'outputs_sha256':sha(canonical(outputs)),'started_at_utc':ts,'duration_seconds':time.monotonic()-tick,'execution':'Python exec of this exact cell source on the declared retained inputs; no notebook-wide execution','before_outputs':original.get('outputs',[]),'after_outputs':outputs}
 receipts.append(record);nb['cells'][index]['outputs']=outputs
 nb['cells'][index]['execution_count']=None # Executed by this Python runner, not a Jupyter kernel counter.
 nb['cells'][index]['metadata']['scientific_correction']={'date':'2026-11-15','baseline_commit':'1d3b45b','execution':'partial Python reexecution','receipt':f'../../../corrections/scientific_20261115/state_kimi_opus/{args.part}_execution.json','source_sha256':record['source_sha256']}
 path.write_text(json.dumps(nb,indent=1,ensure_ascii=False)+'\n');return outputs,record
if args.part=='kimi':
 for test in [1,2,3,4]:
  execute('state-kimi-r1',test,12)
 namespace['confirmation']=json.load(open(namespace['WORK']/'results/confirm_summary.json'));namespace['contrasts']=pd.DataFrame([{'context':k,**v} for k,v in namespace['confirmation']['contexts'].items()])
 execute('state-kimi-r1',1,16);execute('state-kimi-r1',3,17)
 for filename in ['confirm_summary.json','pooled_gene_bootstrap_draws.csv']:(E/filename).write_bytes((namespace['WORK']/'results'/filename).read_bytes())
else:
 for index in [13,14,15,16]:execute('state-opus-r2',5,index)
 for filename in ['partial_rank_gene_bootstrap_summary.json','partial_rank_gene_bootstrap_draws.csv','gene_sensitivity_split_sha256.csv']:(E/filename).write_bytes((namespace['WORK']/'spectra_run/artifacts'/filename).read_bytes())
receipt={'host':platform.node(),'driver':f'{args.part}_executed_driver.py','driver_sha256':sha(driver_bytes),'elapsed_seconds':time.monotonic()-total_tick,'baseline_commit':'1d3b45b','plan_sha256':plan['plan_sha256'],'execution_started_utc':started,'execution_completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':' '.join(sys.argv),'python':platform.python_version(),'versions':{k:v for k,v in [('numpy',np.__version__),('pandas',pd.__version__),('scipy',scipy.__version__),('statsmodels',statsmodels.__version__),('matplotlib',matplotlib.__version__)]},'input_evidence':'input_evidence.json','full_notebook_reexecution':False,'model_inference':False,'cells':receipts}
(E/f'{args.part}_execution.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+'\n');print('completed',args.part,'records',len(receipts))
