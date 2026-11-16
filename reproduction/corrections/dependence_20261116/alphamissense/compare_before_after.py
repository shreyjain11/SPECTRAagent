"""Compare corrected outputs to the numerical precision saved in the original notebooks."""
from pathlib import Path
import io,json
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent
checks=[];changes=[]
for b in sorted((HERE/'before').iterdir()):
 notebook=next(b.glob('*.ipynb'));n=json.loads(notebook.read_text());out=HERE/'outputs'/b.name
 if not (out/'CURRENT_RESULTS.json').exists():continue
 original=[]
 for i,c in enumerate(n['cells']):
  for j,o in enumerate(c.get('outputs',[])):
   html=o.get('data',{}).get('text/html')
   if not html:continue
   html=''.join(html) if isinstance(html,list) else html
   if '<table' not in html:continue
   for table in pd.read_html(io.StringIO(html)):
    original.append((i,j,table))
 mapping=[('curves.csv',['scheme','method','level'],['mean']),('paired_effects.csv',['subset','scheme','comparison'],['mean']),('depth_controls.csv',['subset'],['rho']),('adjusted_controls.csv',['binning','covariate'],['beta'])]
 for filename,keys,point_columns in mapping:
  if not (out/filename).exists():continue
  current=pd.read_csv(out/filename)
  candidates=[(i,j,t) for i,j,t in original if all(k in t for k in keys+point_columns)]
  # Section6 repeats a smaller subset; use the largest displayed table.
  i,j,previous=max(candidates,key=lambda v:len(v[2]))
  assert len(previous)==len(current),(b.name,filename,len(previous),len(current))
  previous.to_csv(b/('displayed-'+filename),index=False)
  joined=previous.merge(current,on=keys,suffixes=('_before','_after'),validate='one_to_one')
  assert len(joined)==len(current)
  for column in point_columns:
   a=joined[column+'_before'].to_numpy(float);z=joined[column+'_after'].to_numpy(float)
   # HTML dataframe values retain six decimal places; exact original floating values were not preserved.
   difference=np.abs(a-z);finite=np.isfinite(difference)
   maxdiff=float(difference[finite].max()) if finite.any() else 0.
   matches=np.allclose(a,z,atol=5.1e-7,rtol=0,equal_nan=True)
   checks.append({'analysis_id':b.name,'table':filename,'point_estimate':column,'rows':len(joined),'original_notebook_cell':i,'original_output':j,'comparison_scope':'agreement to original displayed six-decimal precision; not exact historical floating-point identity','max_abs_difference':maxdiff,'tolerance':5.1e-7,'matches_original_display_precision':bool(matches)})
  joined.to_csv(out/('before-after-'+filename),index=False)
  changes.append({'analysis_id':b.name,'table':filename,'changed_uncertainty_columns':sorted(set(previous.columns)&set(current.columns)&{'low','high','standard_error','t'}),'removed_iid_columns':sorted(set(previous.columns)-set(current.columns)-{'Unnamed: 0'})})
(HERE/'point-estimate-verification.json').write_text(json.dumps({'comparisons':checks,'uncertainty_schema_changes':changes},indent=2)+'\n')
print('Compared',len(checks),'point-estimate tables at their saved display precision;',sum(not c['matches_original_display_precision'] for c in checks),'show raw-replay differences requiring documented cause')
