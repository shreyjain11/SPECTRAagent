"""Package actual STATE correction runs and register their execution scopes."""
from pathlib import Path
from datetime import datetime
import ast,gzip,hashlib,json,shlex,shutil,socket,sys
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
RUNS=Path(sys.argv[1])
PLOT=Path(sys.argv[2])
def rel(path):return str(Path(path).relative_to(ROOT))
def write(path,obj):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def times(book,cells):
 starts=[];ends=[]
 for i in cells:
  ex=book['cells'][i]['metadata']['execution'];starts.append(ex['iopub.status.busy']);ends.append(ex['iopub.status.idle'])
 return min(starts),max(ends)
def dsec(start,end):return (datetime.fromisoformat(end.replace('Z','+00:00'))-datetime.fromisoformat(start.replace('Z','+00:00'))).total_seconds()
registrations=[]
verification=json.loads((HERE/'state_primary/regression-verification.json').read_text())
for test in [5,9,10,13,14,15,16,17,18,19]:
 name=f'test-{test:02d}';identifier='state-featured/'+name;path=ROOT/f'inline/state/state-featured/{name}.ipynb';book=json.loads(path.read_text())
 work=RUNS/name;out=work/'state_primary_outputs'/name;dest=HERE/'state_primary/outputs'/name;dest.mkdir(parents=True,exist_ok=True)
 artifact_paths=[]
 for filename in ['curve.csv','trends.csv','execution_record.json','adjusted_coefficients.csv','annotated_extreme_contrasts.csv','pathway_count_strata.csv']:
  if (out/filename).exists():shutil.copy(out/filename,dest/filename);artifact_paths.append(rel(dest/filename))
 shutil.copy(work/'runner.log',dest/'runner.log')
 write(dest/'adjusted_support_verification.json',[r for r in verification if r['analysis_id']==identifier]);artifact_paths.append(rel(dest/'adjusted_support_verification.json'))
 execution=json.loads((out/'execution_record.json').read_text())
 write(dest/'verified_source_manifest.json',{'source_files':execution['source_files'],'upstream_method':'Notebook verifies each extracted cached source against its pinned byte count and SHA-256 before parsing. The two source archives and four split files below contain those exact bytes.'})
 artifact_paths.append(rel(dest/'verified_source_manifest.json'))
 cells=[i for i,c in enumerate(book['cells']) if c['cell_type']=='code'];start,end=times(book,cells)
 inputs=[{'path':'primary/state/payloads/state-official-score-cache.tar.gz','role':'Public archive containing the exact official-score bytes verified by the notebook'}, {'path':'primary/state/payloads/state-historical-annotations.tar.gz','role':'Public archive containing the exact historical annotation bytes verified by the notebook'}]
 for context in ['hepg2','jurkat','k562','rpe1']:
  inputs.append({'path':'primary/state/original/state_generalizability_20260602_single_controller/external/state/state_preprint_toml_files/replogle_tomls/'+context+'.toml','role':'Pinned context split definition'})
 registrations.append({'analysis_id':identifier,'mode':'full_notebook','executed_notebook_cells':cells,
 'summary':'Corrected redundant regression controls and canonical-gene-clustered uncertainty.',
 'execution':{'host':book['metadata']['analysis_execution']['host'],'python':book['metadata']['language_info']['version'],'started_at':start,'finished_at':end,'elapsed_seconds':book['metadata']['analysis_execution']['elapsed_seconds'],
 'command':shlex.join(['env','STATE_PRIMARY_INPUTS=/private/tmp/state-primary-correction-inputs',book['metadata']['analysis_execution']['python'],str(ROOT/'inline/execute_notebook.py'),str(path),'--cwd',str(work),'--timeout','600']),'driver':'inline/execute_notebook.py','log':rel(dest/'runner.log')},
 'inputs':inputs,'output_artifacts':artifact_paths,
 'dependency_scope':'Every code cell rerun from pinned, hash-verified cached public score, annotation and split inputs. The source archives and split files bind the consumed bytes; verified_source_manifest.json identifies each extracted source. Released model scores reused; no fresh STATE inference. Cohort, axis and outcome definitions unchanged.'})
# The plot rerun has its own exact prerequisite setup and input file.
plotdest=HERE/'state_plot/outputs';plotdest.mkdir(parents=True,exist_ok=True)
for name in ['corrected_curve.csv','controls_curve.png','numerical_check.json']:
 shutil.copy(PLOT/name,plotdest/name)
runner=json.loads((PLOT/'executed_plot_correction.ipynb').read_text())
start,end=times(runner,[0,1,2]);selected=21
log={'completed':True,'execution_scope':'selected_plot_cell','host':socket.gethostname(),'python':runner['metadata']['language_info']['version'],'started_at':start,'finished_at':end,'executed_cells_in_helper':[0,1,2],'published_notebook_cell':21,'comparison':json.loads((PLOT/'numerical_check.json').read_text())}
write(plotdest/'execution.json',log)
input_path='reconstructed/state-codex-r1/computed/analysis/controls/per_condition_scores.csv'
registrations.append({'analysis_id':'state-codex-r1/test-04','mode':'selected_cells','executed_notebook_cells':[21],
 'summary':'Corrected the S-phase plot label; recomputed points and intervals match the prior displayed values.',
 'execution':{'host':socket.gethostname(),'python':runner['metadata']['language_info']['version'],'started_at':start,'finished_at':end,'elapsed_seconds':dsec(start,end),
 'command':shlex.join([sys.executable,str(HERE/'state_plot/rerun_plot.py'),str(PLOT)]),'driver':'corrections/scientific_20261115/state_plot/rerun_plot.py','log':rel(plotdest/'execution.json')},
 'inputs':[{'path':input_path,'role':'Retained per-condition model/reference scores and S-phase axis values','rows':17040}],
 'prerequisite_setup':{'script':'corrections/scientific_20261115/state_plot/rerun_plot.py','input_paths':[input_path],'description':'Restore hvg_best confirmation records and join S-phase SD by cell line; execute the actual corrected plot cell with the original seed and bootstrap repetitions.'},
 'output_artifacts':[rel(plotdest/x) for x in ['corrected_curve.csv','controls_curve.png','numerical_check.json']],
 'dependency_scope':'Only cell 21 reexecuted from retained per-condition scores (4020 confirmation records, 268 compounds across five contexts). Every plotted point/interval checked against prior output at its six-decimal display precision. All other scientific cells and outputs remain byte-identical to the previous revision.'})
write(HERE/'root_registration.json',registrations)
print('Registered',len(registrations),'executed corrections')
