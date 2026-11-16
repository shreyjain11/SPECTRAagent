"""Integrate the seven dependence corrections while preserving original receipts."""
import argparse,gzip,hashlib,html,importlib.util,json,os,re,subprocess,sys
from pathlib import Path
import nbformat
from nbconvert import HTMLExporter
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASE='01461707b4c37faba205b053c4c623a58cbd0cb1'
sys.path.insert(0,str(ROOT))
from integrate_inline import code_review,html_page,markdown_index
from validate_scientific_revision import code_cells
spec=importlib.util.spec_from_file_location('layout',ROOT/'review_20261115/update_presentation.py');layout=importlib.util.module_from_spec(spec);spec.loader.exec_module(layout)
def sha(data):return hashlib.sha256(data).hexdigest()
def read(path):return json.loads((ROOT/path).read_text())
def write(path,obj):
 p=ROOT/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def asset(path,**extra):
 p=ROOT/path;return {'path':str(path),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size,**extra}
def original(path):return subprocess.check_output(['git','show',f'{BASE}:reproduction/{path}'],cwd=ROOT.parent)
def integrate(reg):
 identifier=reg['analysis_id'];record_path='analyses/'+identifier+'.json'
 record=read(record_path);impl=record['inline_implementation'];notebook=impl['notebook'];page=impl['html'];receipt_path=impl['execution_evidence']
 b=json.loads((ROOT/notebook).read_text());prior_bytes=original(notebook);prior=json.loads(prior_bytes)
 b['metadata'].pop('execution_verification',None)
 if reg['mode']=='selected_cells':
  b['metadata'].pop('analysis_execution',None)
 b['metadata']['scientific_correction']={'mode':reg['mode'],'executed_notebook_cells':reg['executed_notebook_cells'],
  'host':reg['execution']['host'],'previous_commit':BASE}
 (ROOT/notebook).write_text(json.dumps(b,indent=1,ensure_ascii=False)+'\n')
 old_receipt_bytes=original(receipt_path);old_receipt=json.loads(old_receipt_bytes)
 base='corrections/dependence_20261116/records/'+identifier.replace('/','-')
 gz=ROOT/(base+'.original.ipynb.gz');gz.parent.mkdir(parents=True,exist_ok=True);gz.write_bytes(gzip.compress(prior_bytes,mtime=0))
 (ROOT/(base+'.previous-execution.json')).write_bytes(old_receipt_bytes)
 revision_path=base+'.scientific-revision.json'
 title=next(''.join(c['source']).splitlines()[0].removeprefix('# ') for c in b['cells'] if c['cell_type']=='markdown')
 page_html,_=HTMLExporter(template_name='lab').from_notebook_node(nbformat.reads(json.dumps(b),as_version=4),resources={'metadata':{'name':title}})
 page_html=layout.output_typography(page_html)
 page_html=re.sub(r'<title>.*?</title>','<title>'+html.escape(title)+'</title>',page_html,count=1,flags=re.S)
 page_html=page_html.replace('</head>','<style id="spectra-notebook-layout">'+layout.CSS+'</style>\n</head>',1)
 href=os.path.relpath(ROOT/revision_path,(ROOT/page).parent)
 note=('All code cells rerun.' if reg['mode']=='full_notebook' else 'Affected calculations rerun from retained records; other outputs retain their earlier execution.')
 nav='<nav class="notebook-navigation"><a href="../../index.html">All notebooks</a> · <a href="'+html.escape(href,quote=True)+'">Correction record</a><p>'+html.escape(reg['summary']+' '+note)+'</p></nav>'
 page_html=re.sub(r'(<body\b[^>]*>)',lambda m:m[1]+'\n'+nav,page_html,count=1)
 (ROOT/page).write_text(page_html)
 direct=reg['executed_notebook_cells'] if reg['execution'].get('engine')=='python_exec' else ()
 sections,indices=code_review(b,direct_executed_cells=direct);indices=list(indices)
 before,after=code_cells(prior),code_cells(b)
 executed=reg['executed_notebook_cells']
 changed=[i for i,c in enumerate(b['cells']) if c['cell_type']=='code' and (i>=len(prior['cells']) or c!=prior['cells'][i])]
 mode=reg['mode'];execution=dict(reg['execution'])
 if execution.get('engine') == 'nbclient':
  execution.update(engine='jupyter', executor='nbclient')
 execution={**execution,'driver':asset(execution['driver']),'log':asset(execution['log'])}
 result=impl['calculated_result'];section6=next(s for s in sections if s['number']==6)
 result['code_cells']=section6['code_cells']
 if 'interpretation' in result:result['interpretation']['markdown_cell']=section6['markdown_cell']
 revision={'schema_version':1,'analysis_id':identifier,'scientific_reexecution':True,'mode':mode,'reason':reg['summary'],'original_commit':BASE,
 'original_artifacts':{'notebook':{'path':notebook,'sha256':sha(prior_bytes)},'html':{'path':page,'sha256':old_receipt['html_sha256']}},
 'published_artifacts':{'notebook':asset(notebook),'html':asset(page)},'original_code_cells':before,'published_code_cells':after,
 'executed_notebook_cells':executed,'changed_code_cells':changed,'executed_cell_evidence':[r for r in after if r['notebook_cell'] in executed],
 'execution':execution,'inputs':[asset(x['path'],**{k:v for k,v in x.items() if k not in ['path','sha256','bytes']}) for x in reg['inputs']],
 'output_artifacts':[asset(x) for x in reg['output_artifacts']],'dependency_scope':reg['dependency_scope']}
 if mode=='selected_cells':
  q=reg['prerequisite_setup'];revision['prerequisite_setup']={**q,'script':asset(q['script'])}
 write(revision_path,revision)
 receipt={'analysis_id':identifier,'notebook':notebook,'html':page,'completed':True,'host':execution['host'],'python':execution['python'],
 'elapsed_seconds':execution['elapsed_seconds'],'execution_scope':{'full_notebook':'full_notebook_reexecuted','selected_cells':'selected_cells_reexecuted'}[mode],
 'code_cells':len(after),'executed_cells':len(executed),'errors':0,'notebook_sha256':sha((ROOT/notebook).read_bytes()),'html_sha256':sha((ROOT/page).read_bytes()),
 'sections':sections,'cell_index_base':0,'result_location':result,'embedded_figures':sum('image/png' in output.get('data', {}) for cell in b['cells'] for output in cell.get('outputs', [])),
 'checks':['scientific_revision_artifacts_and_executed_cell_hashes','unchanged_cells_match_archived_notebook','no_error_outputs','six_sections_and_inline_code'],
 'scientific_revision':{'schema_version':1,'scientific_reexecution':True,'mode':mode,'previous_execution_evidence':asset(base+'.previous-execution.json'),
 'original_notebook_snapshot':asset(base+'.original.ipynb.gz',compression='gzip',notebook_sha256=sha(prior_bytes)),'record':asset(revision_path)}}
 if mode=='full_notebook':receipt['checks'].append('all_code_cells_executed')
 write(receipt_path,receipt)
 impl.update(published_notebook_sha256=receipt['notebook_sha256'],published_html_sha256=receipt['html_sha256'],sections=sections,code_cells=len(after),calculated_result=result)
 current=record['current_inline_analysis'];current.update(notebook_sha256=receipt['notebook_sha256'],verification_boundary=reg['dependency_scope'],scientific_correction={'record':revision_path,'execution_scope':receipt['execution_scope'],'summary':reg['summary']})
 current.pop('interpretation_review',None)
 if 'evidence' in current:current['evidence'].update(notebook_sha256=receipt['notebook_sha256'],execution_record_sha256=sha((ROOT/receipt_path).read_bytes()))
 write(record_path,record)
 return {'id':identifier,'mode':mode,'executed_notebook_cells':executed,'revision':revision_path}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('registration',nargs='+',type=Path);a=p.parse_args()
 registrations=[]
 for path in a.registration:
  data=json.loads(path.read_text());registrations+=data if isinstance(data,list) else data['entries']
 results=[integrate(r) for r in registrations]
 write('corrections/dependence_20261116/integrated.json',results)
 index=read('inline/index.json')
 for row in index['analyses']:
  matching=[x for x in results if x['id']==row['id']]
  if matching:row['scientific_correction']=matching[0]
 write('inline/index.json',index)
 (ROOT/'inline/index.html').write_text(html_page(index['analyses']))
 (ROOT/'inline/INDEX.md').write_text(markdown_index(index['analyses']))
 print('Integrated',len(results),'scientific corrections')
