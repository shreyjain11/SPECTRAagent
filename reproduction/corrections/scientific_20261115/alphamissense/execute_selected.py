"""Execute corrected scientific cells against explicit public-derived records.

Usage: python .../execute_selected.py /path/to/retained_rebuild
Only the two named cells per notebook are reexecuted. The setup reconstructs
inputs from public payloads; it does not rerun acquisition or raw clustering.
"""
from pathlib import Path
from io import BytesIO
from collections import Counter,defaultdict
from datetime import datetime,timezone
import sys,os,json,hashlib,gzip,time,platform,subprocess,shutil
import numpy as np,pandas as pd
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from IPython.core.interactiveshell import InteractiveShell
from IPython.utils.capture import capture_output
from IPython.display import display,Image,Markdown
import nbformat
InteractiveShell.instance()
HERE=Path(__file__).resolve().parent;R=HERE.parents[2];REPO=R.parent
CACHE=Path(sys.argv[1]).resolve()
BASE=subprocess.check_output(['git','rev-parse','1d3b45b'],cwd=REPO,text=True).strip()
def sha256_file(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def artifact(p,**extras):return {'path':str(Path(p).relative_to(R)),'sha256':sha256_file(p),'bytes':Path(p).stat().st_size,**extras}
def show_figure(fig):
    b=BytesIO();fig.savefig(b,format='png',dpi=150,bbox_inches='tight');display(Image(data=b.getvalue()))
inputs=HERE/'inputs';inputs.mkdir(exist_ok=True)
panel=pd.read_pickle(CACHE/'candidate_panel.pkl')
panel.to_csv(inputs/'individual_variants.csv.gz',index=False,compression={'method':'gzip','mtime':0})
for src,dest in [('candidate_coverage.csv','score_join_coverage.csv'),('candidate_position_features.csv','position_features.csv')]:shutil.copyfile(CACHE/src,inputs/dest)
# Read the exact published calculation input with round-trip float parsing.
panel=pd.read_csv(inputs/'individual_variants.csv.gz',float_precision='round_trip')
assert len(panel)==270572 and panel.assay.nunique()==72 and panel.accession.nunique()==63
coverage=pd.read_csv(inputs/'score_join_coverage.csv',float_precision='round_trip')
position_features=pd.read_csv(inputs/'position_features.csv',float_precision='round_trip')
archives=[R/'primary/alphamissense/payloads'/name for name in ['am-frozen-panel-and-score-inputs.tar.gz','am-original-dms-members.tar.gz','am-recorded-alignment-results.tar.gz']]
source_receipts=[{'path':str(p.relative_to(R)),'url':f'https://raw.githubusercontent.com/shreyjain11/SPECTRAagent/{BASE}/reproduction/{p.relative_to(R)}','sha256':sha256_file(p),'bytes':p.stat().st_size} for p in archives]
records=[]
for axis in range(3,8):
    path=R/f'inline/alphamissense/am-primary/axis-{axis}.ipynb'
    original_bytes=subprocess.check_output(['git','show',f'{BASE}:{path.relative_to(REPO)}'],cwd=REPO)
    original=json.loads(original_bytes)
    before=HERE/'before'/f'axis-{axis}';before.mkdir(parents=True,exist_ok=True)
    (before/'original.ipynb.gz').write_bytes(gzip.compress(original_bytes,mtime=0))
    receipt_path=path.with_suffix('.execution.json')
    (before/'previous-execution.json').write_bytes(subprocess.check_output(['git','show',f'{BASE}:{receipt_path.relative_to(REPO)}'],cwd=REPO))
    book=json.loads(path.read_text());indices=[i for i,c in enumerate(book['cells']) if c['cell_type']=='code' and (''.join(c['source']).startswith('AXIS_NUMBER=') or ''.join(c['source']).startswith('selected=contrasts['))]
    assert len(indices)==2
    outdir=HERE/'outputs'/f'axis-{axis}';outdir.mkdir(parents=True,exist_ok=True)
    start=datetime.now(timezone.utc).isoformat();began=time.monotonic()
    context=dict(panel=panel,coverage=coverage,position_features=position_features,np=np,pd=pd,spearmanr=spearmanr,plt=plt,display=display,show_figure=show_figure,OUTPUT=outdir,WEIGHTED=False,source_receipts=source_receipts,sha256_file=sha256_file,platform=platform,time=time,STARTED=time.time(),json=json,os=os)
    logs=[]
    for count,i in enumerate(indices,1):
        source=''.join(book['cells'][i]['source'])
        # Record a reproducible compressed export; statistical values are unchanged.
        source=source.replace("compression='gzip'","compression={'method':'gzip','mtime':0}")
        book['cells'][i]['source']=source.splitlines(True)
        with capture_output() as captured:exec(compile(source,f'axis-{axis}:cell-{i}','exec'),context)
        outputs=[]
        if captured.stdout:outputs.append(nbformat.v4.new_output('stream',name='stdout',text=captured.stdout))
        if captured.stderr:outputs.append(nbformat.v4.new_output('stream',name='stderr',text=captured.stderr))
        for o in captured.outputs:outputs.append(nbformat.v4.new_output('display_data',data=o.data,metadata=o.metadata))
        book['cells'][i]['outputs']=[dict(o) for o in outputs];book['cells'][i]['execution_count']=count
        logs.append(f'EXECUTED notebook cell {i}\nSOURCE SHA256 {hashlib.sha256(source.encode()).hexdigest()}\n'+captured.stdout+captured.stderr+f'CAPTURED rich outputs: {len(captured.outputs)}\n')
    elapsed=time.monotonic()-began;finished=datetime.now(timezone.utc).isoformat()
    # Verify no unexecuted scientific cell, including metadata, was changed.
    for i,(old,new) in enumerate(zip(original['cells'],book['cells'])):
        if old['cell_type']=='code' and i not in indices:assert old==new,(axis,i)
    assert len(book['cells'])==len(original['cells'])
    path.write_text(json.dumps(book,indent=1,ensure_ascii=False)+'\n')
    (outdir/'execution.log').write_text('START '+start+'\n'+''.join(logs)+'END '+finished+'\n')
    context['curves'].to_csv(outdir/'corrected_curves.csv',index=False)
    context['contrasts'].to_csv(outdir/'corrected_contrasts.csv',index=False)
    contrast=context['contrasts'];sel=contrast[(contrast.score=='am')&(contrast['first']==context['LEVELS'][0])&(contrast['last']==context['LEVELS'][-1])]
    record={'analysis_id':f'am-primary/test-{axis:02d}','original_commit':BASE,'mode':'selected_cells','executed_notebook_cells':indices,'changed_code_cells':indices,'original_notebook_snapshot':artifact(before/'original.ipynb.gz',compression='gzip',notebook_sha256=hashlib.sha256(original_bytes).hexdigest()),'previous_execution_evidence':artifact(before/'previous-execution.json'),'execution':{'host':platform.node(),'python':platform.python_version(),'elapsed_seconds':elapsed,'started_at':start,'finished_at':finished,'command':'python reproduction/corrections/scientific_20261115/alphamissense/execute_selected.py /private/tmp/am-primary-scientific-20261115','driver':artifact(Path(__file__)),'log':artifact(outdir/'execution.log')},'inputs':[artifact(inputs/'individual_variants.csv.gz',rows=len(panel),role='Actual scored DMS records and retained alignment-derived features consumed by the rerun'),artifact(inputs/'score_join_coverage.csv'),artifact(inputs/'position_features.csv')]+[artifact(p,role='Public source payload used to rebuild calculation inputs') for p in archives],'prerequisite_setup':{'script':artifact(HERE/'rebuild_retained_inputs.py'),'input_paths':[str(p.relative_to(R)) for p in archives],'description':'Rebuilt the original selected DMS variant/score join and retained alignment features from public payloads, then restored the panel, coverage and position-feature globals before executing the two recorded notebook cells. No fresh clustering or inference.'},'output_artifacts':[artifact(p) for p in sorted(outdir.iterdir()) if p.is_file()],'dependency_scope':'Only the per-assay statistic/aggregation/plot cell and decision/export cell were executed now. Other scientific cells retain exact earlier code and outputs. Recorded profiles replace fresh clustering only for this declared recalculation; a small PSSM reference difference is documented.','decision':context['decision'],'primary_endpoint':json.loads(sel.to_json(orient='records'))}
    records.append(record)
    print(axis,context['decision'],flush=True)
(HERE/'execution-evidence.json').write_text(json.dumps({'schema_version':1,'scope':'Selected scientific-cell reexecution from public retained records','entries':records},indent=2)+'\n')
