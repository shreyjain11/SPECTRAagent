"""Replay two exact original notebooks under the same current input/environment.

This isolates upstream numerical replay differences from the statistical repair.
It does not alter the corrected notebooks or the immutable original snapshots.
"""
from pathlib import Path
import concurrent.futures,datetime,gzip,hashlib,json,os,platform,shutil,subprocess,sys,time
HERE=Path(__file__).resolve().parent
WORK=Path('/private/tmp/am-opus-original-method-replay-20261116')
CACHE=Path('/private/tmp/am-opus-dependence-inputs-20261116')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def run(test):
 slug='am-opus-r1-test-'+test;work=WORK/slug;work.mkdir(parents=True,exist_ok=True)
 source=HERE/'before'/slug/('test-'+test+'.ipynb');book=work/'original.ipynb';shutil.copyfile(source,book)
 assert sha(source)==sha(book)
 command=[sys.executable,str(HERE/'execute_notebook.py'),str(book),'--cwd',str(work),'--timeout','3600']
 start=utc();t=time.monotonic();print('START original',slug,start,flush=True)
 env=dict(os.environ,AM_OPUS_INPUTS=str(CACHE),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
 proc=subprocess.run(command,env=env,capture_output=True,text=True)
 finish=utc();elapsed=time.monotonic()-t
 out=HERE/'original-method-replays'/slug;out.mkdir(parents=True,exist_ok=True)
 (out/'execution.log').write_text('START '+start+'\n'+proc.stdout+proc.stderr+'\nEND '+finish+'\n')
 assert proc.returncode==0,proc.stdout[-2500:]
 n=json.loads(book.read_text());codes=[i for i,c in enumerate(n['cells']) if c['cell_type']=='code'];assert all(n['cells'][i]['execution_count'] is not None for i in codes)
 orig=json.loads(source.read_text());assert all(''.join(n['cells'][i]['source'])==''.join(orig['cells'][i]['source']) for i in range(len(n['cells'])))
 (out/'executed-original.ipynb.gz').write_bytes(gzip.compress(book.read_bytes(),mtime=0))
 generated=work/(slug+'-outputs')
 for p in generated.glob('*.csv'):shutil.copyfile(p,out/p.name)
 data={'analysis_id':'am-opus-r1/test-'+test,'host':platform.node(),'python':platform.python_version(),'started_at':start,'finished_at':finish,'elapsed_seconds':elapsed,'executed_notebook_cells':codes,'source_notebook_sha256':sha(source),'executed_notebook_sha256':sha(book),'scientific_source_unchanged':True,'input_cache':str(CACHE),'command':command,'role':'Exact original-method full replay on the same pinned public sources and present environment; not the historical execution'}
 (out/'execution.json').write_text(json.dumps(data,indent=2)+'\n')
 print('DONE original',slug,round(elapsed,1),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:list(pool.map(run,['01','03']))
