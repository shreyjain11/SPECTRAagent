"""Check seven current pages, metadata and receipt integrity after integration."""
import base64,datetime,gzip,hashlib,json,pathlib,re,subprocess
from bs4 import BeautifulSoup
from nbconvert.filters import markdown2html
HERE=pathlib.Path(__file__).resolve().parent
REPO=HERE.parents[3];R=REPO/'reproduction'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
normalize=lambda s:' '.join(s.split()).replace('¶','').strip()
ids=[f'am-opus-r{r}/test-{t:02d}' for r in [1,2] for t in [1,2,3]]+['state-featured/test-03']
combined=load(R/'corrections/dependence_20261116/alphamissense/current_results.json')
checks=[];issues=[]
for ident in ids:
 analysis=load(R/'analyses'/(ident+'.json'));inline=analysis['inline_implementation'];current=analysis['current_inline_analysis']
 path=R/inline['notebook'];book=load(path);receipt=load(R/inline['execution_evidence']);page_path=R/inline['html'];page=BeautifulSoup(page_path.read_text(),'html.parser')
 assert sha(path)==receipt['notebook_sha256']==inline['published_notebook_sha256']==current['notebook_sha256']
 assert sha(page_path)==receipt['html_sha256']==inline['published_html_sha256']
 code=[(i,c) for i,c in enumerate(book['cells']) if c['cell_type']=='code'];md=[(i,c) for i,c in enumerate(book['cells']) if c['cell_type']=='markdown']
 assert [c['execution_count'] for i,c in code]==list(range(1,len(code)+1))
 assert receipt['execution_scope']=='full_notebook_reexecuted' and receipt['executed_cells']==len(code)
 assert not any(o.get('output_type')=='error' for i,c in code for o in c.get('outputs',[]))
 sources=page.select('.jp-CodeCell .jp-InputArea .highlight pre');assert len(sources)==len(code)
 for (_,cell),el in zip(code,sources):assert el.get_text().rstrip('\n')==''.join(cell['source']).rstrip('\n')
 rendered_md=page.select('.jp-MarkdownCell .jp-RenderedHTMLCommon');assert len(rendered_md)==len(md),(ident,len(rendered_md),len(md))
 for (i,cell),el in zip(md,rendered_md):
  expected=normalize(BeautifulSoup(markdown2html(''.join(cell['source'])),'html.parser').get_text())
  actual=normalize(el.get_text());assert expected==actual,(ident,i,expected[:120],actual[:120])
 # Confirm actual images are the saved scientific outputs, excluding notebook CSS assets.
 images=[base64.b64decode(''.join(o['data']['image/png'])) for i,c in code for o in c.get('outputs',[]) if 'image/png' in o.get('data',{})]
 html_images=[base64.b64decode(x['src'].split(',',1)[1]) for x in page.find_all('img') if x.get('src','').startswith('data:image/png;base64,')]
 assert images==html_images
 if receipt['embedded_figures']!=len(images):issues.append({'id':ident,'issue':'embedded_figures count includes non-figure CSS asset','receipt_count':receipt['embedded_figures'],'actual_notebook_png_outputs':len(images)})
 revision=receipt['scientific_revision']
 for field in ['previous_execution_evidence','original_notebook_snapshot','record']:
  item=revision[field];p=R/item['path'];assert sha(p)==item['sha256'] and p.stat().st_size==item['bytes']
 previous=load(R/revision['previous_execution_evidence']['path']);oldbytes=gzip.decompress((R/revision['original_notebook_snapshot']['path']).read_bytes());assert hashlib.sha256(oldbytes).hexdigest()==previous['notebook_sha256']
 correction=load(R/revision['record']['path'])
 # Current metadata is bound to actual calculated outputs, not the archived pre-correction result.
 if ident.startswith('am-'):
  data=combined[ident];assert current['curve']['reported_result']==data['reported_result'];assert current['insight']['comparator_contrasts']==data['comparator_contrasts']
  assert current['insight']['interpretation'].startswith(data['decision'])
  binding=current['evidence']['statistical_result'];assert sha(R/binding['path'])==binding['sha256']
  text=json.dumps(current)
  assert 'bootstrap assays (' not in text and 'wilcoxon_p' not in text
  assert current['model_evaluation']['fresh_target_inference'] is False
  assert current['model_evaluation']['target_fine_tuning'] is False
 else:
  numerical=load(HERE/'state-numerical-review.json')
  lookup={(x['subset'],x['representation']):x for x in numerical['strata']}
  for value in current['curve']['contrasts']:
   actual=lookup[(value['subset'],value['representation'])];assert abs(value['estimate']-actual['point'])<1e-12
   assert max(abs(x-y) for x,y in zip(value['confidence_interval_95'],actual['ci95']))<1e-12
   assert value['populated_annotated_levels']==2
  assert 'not a validated three-level curve or full protocol acceptance' in current['insight']['interpretation']
 checks.append({'id':ident,'all_code_cells_executed':len(code),'markdown_cells_rendered_verbatim':len(md),'scientific_code_rendered_verbatim':True,'saved_png_outputs_match_HTML':len(images),'current_notebook_HTML_receipt_metadata_hashes_agree':True,'original_notebook_and_previous_receipt_preserved':True,'current_metadata_matches_verified_result':True,'receipt_scientific_revision_record':revision['record']['path']})
result={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'analyses':checks,'issues':issues,'scope':'Seven corrected entries only; technical consistency and independent numerical verification do not establish fresh inference, original discovery chronology, independent external confirmation or all-protocol completion.','historical_replay_boundary':'AM r1 test01/test03 show small differences from old displayed numbers; exact original intermediate assay tables were not retained. Original formulas on the current inputs reproduce the corrected point estimates to machine precision.'}
(HERE/'final-integration-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'entries':len(checks),'code_cells':sum(x['all_code_cells_executed'] for x in checks),'markdown_cells':sum(x['markdown_cells_rendered_verbatim'] for x in checks),'images':sum(x['saved_png_outputs_match_HTML'] for x in checks),'issues':issues},indent=2))
