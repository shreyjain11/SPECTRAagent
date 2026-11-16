"""Execute a notebook in a clean Jupyter kernel and retain actual execution evidence."""
from pathlib import Path
from datetime import datetime, timezone
import argparse, hashlib, json, os, platform, socket, subprocess, sys, time

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('phase', choices=['before', 'after']); a=p.parse_args()
    work = Path('/private/tmp/state-test03-dependence-20261116') / a.phase
    notebook = work/'original.ipynb' if a.phase == 'before' else ROOT/'reproduction/inline/state/state-featured/test-03.ipynb'
    command = [sys.executable, str(ROOT/'reproduction/inline/execute_notebook.py'), str(notebook), '--cwd', str(work), '--timeout', '600']
    env = {**os.environ, 'STATE_PRIMARY_INPUTS':'/private/tmp/state-primary-correction-inputs', 'PYTHONHASHSEED':'0', 'OPENBLAS_NUM_THREADS':'1', 'OMP_NUM_THREADS':'1'}
    start = datetime.now(timezone.utc).isoformat(); timer=time.monotonic(); before=sha(notebook)
    result = subprocess.run(command, env=env, capture_output=True, text=True)
    finish=datetime.now(timezone.utc).isoformat(); elapsed=time.monotonic()-timer
    log = HERE / (a.phase+'.log');log.write_text(result.stdout+result.stderr)
    book=json.loads(notebook.read_text())
    record={'phase':a.phase,'completed':result.returncode==0,'return_code':result.returncode,'host':socket.gethostname(),'python':sys.version,'python_executable':sys.executable,'platform':platform.platform(),'engine':'jupyter','started_at':start,'finished_at':finish,'elapsed_seconds':elapsed,'command':command,'working_directory':str(work),'environment':{k:env[k] for k in ['STATE_PRIMARY_INPUTS','PYTHONHASHSEED','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS']},'driver_sha256':sha(__file__),'shared_runner_sha256':sha(ROOT/'reproduction/inline/execute_notebook.py'),'notebook_before_sha256':before,'notebook_after_sha256':sha(notebook),'executed_notebook_cells':[i for i,c in enumerate(book['cells']) if c['cell_type']=='code' and c['execution_count'] is not None],'cell_execution':[{'index':i,'execution_count':c['execution_count'],'timing':c.get('metadata',{}).get('execution',{}),'error_outputs':[o for o in c.get('outputs',[]) if o.get('output_type')=='error']} for i,c in enumerate(book['cells']) if c['cell_type']=='code'],'stdout_stderr_sha256':sha(log)}
    (HERE/(a.phase+'-execution.json')).write_text(json.dumps(record,indent=2)+'\n')
    print(result.stdout);print(result.stderr);print('Execution evidence:',HERE/(a.phase+'-execution.json'))
    raise SystemExit(result.returncode)
