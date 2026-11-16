"""Independent checks of the correction and its unchanged scientific target."""
from pathlib import Path
from io import StringIO
import json,gzip,hashlib,importlib.util,subprocess
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;R=HERE.parents[2]
spec=importlib.util.spec_from_file_location('protein_bootstrap',HERE/'protein_bootstrap.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def add(name,detail):checks.append({'check':name,'detail':detail})
# A single assay, or several assays of one protein, cannot estimate protein uncertainty.
for d in [pd.DataFrame({'protein':['p'],'value':[.523308]}),pd.DataFrame({'protein':['p','p'],'value':[.2,.8]})]:
 x=m.protein_cluster_interval(d,'value',rng=np.random.default_rng(42));assert np.isnan(x['ci_low']) and np.isnan(x['ci_high']) and x['bootstrap_proteins']==1
add('single-protein guard','One assay and multiple assays of one protein both return unavailable intervals.')
d=pd.DataFrame({'protein':['a','a','b'],'value':[0.,1.,2.],'weight':[2.,3.,4.]})
result=m.protein_cluster_interval(d,'value','weight',rng=np.random.default_rng(19))
rng=np.random.default_rng(19);names=np.array(['a','b']);draws=[]
for ids in rng.integers(0,2,size=(5000,2)):
 selected=pd.concat([d[d.protein==names[i]] for i in ids],ignore_index=True)
 draws.append(np.average(selected.value,weights=selected.weight))
assert np.allclose([result['ci_low'],result['ci_high']],np.quantile(draws,[.025,.975]),atol=1e-15)
add('whole-cluster resampling','Helper matches explicit row concatenation when one protein has repeated assays and unequal weights.')
x=m.protein_cluster_interval(pd.DataFrame({'protein':['a','b'],'value':[1.,1.]}),'value',rng=np.random.default_rng(1))
assert np.isnan(x['ci_low']) and x['ci_status']=='no_empirical_resampling_variation'
add('constant resampling guard','No zero-width empirical interval is emitted for an unvarying cluster distribution.')
comparison=[]
for axis in range(3,8):
 before=json.loads(gzip.decompress((HERE/'before'/f'axis-{axis}'/'original.ipynb.gz').read_bytes()))
 tables=[]
 for c in before['cells']:
  for o in c.get('outputs',[]):
   if 'text/html' in o.get('data',{}):tables.extend(pd.read_html(StringIO(''.join(o['data']['text/html']))))
 old_curve=next(t for t in tables if 'weighted_abs_rho' in t.columns and 'ci_low' in t.columns)
 old_contrast=next(t for t in tables if 'paired_assays' in t.columns)
 output=HERE/'outputs'/f'axis-{axis}'
 new_curve=pd.read_csv(output/'curves.csv');new_contrast=pd.read_csv(output/'contrasts.csv')
 old_curve.to_csv(HERE/'before'/f'axis-{axis}'/'displayed_curves.csv',index=False)
 old_contrast.to_csv(HERE/'before'/f'axis-{axis}'/'displayed_contrasts.csv',index=False)
 curves=old_curve.merge(new_curve,on=['level','score'],suffixes=('_before','_after'),validate='one_to_one');assert len(curves)==len(old_curve)==len(new_curve)
 for count in ['assays','proteins','variants']:assert (curves[count+'_before']==curves[count+'_after']).all()
 # PSSM is the explicitly documented retained-profile-route difference.
 non_pssm=curves[curves.score!='pssm'];assert (abs(non_pssm.weighted_abs_rho_before-non_pssm.weighted_abs_rho_after)<=5.1e-7).all()
 c=old_contrast.merge(new_contrast,on=['score','first','last'],suffixes=('_before','_after'),validate='one_to_one');assert (c.paired_assays_before==c.paired_assays_after).all()
 non_pssm=c[c.score!='pssm'];assert (abs(non_pssm.mean_last_minus_first_before-non_pssm.mean_last_minus_first_after)<=5.1e-7).all()
 verification_dir=HERE/'verification_tables'/f'axis-{axis}';verification_dir.mkdir(parents=True,exist_ok=True)
 c.to_csv(verification_dir/'before_after_contrasts.csv',index=False);curves.to_csv(verification_dir/'before_after_curves.csv',index=False)
 per=pd.read_csv(output/'per_assay.csv')
 for row in new_contrast.itertuples():
  d=per[per.score==row.score];w=d.pivot(index='assay',columns='level',values='abs_rho');diff=(w[row.last]-w[row.first]).dropna();proteins=d.groupby('assay').protein.first().reindex(diff.index)
  assert len(diff)==row.paired_assays and proteins.nunique()==row.paired_proteins
  assert abs(diff.mean()-row.mean_last_minus_first)<1e-12
  if row.paired_proteins<2:assert pd.isna(row.ci_low) and pd.isna(row.ci_high)
 comparison.append({'axis':axis,'curve_rows':len(curves),'max_curve_point_difference_from_displayed_before':float(abs(curves.weighted_abs_rho_before-curves.weighted_abs_rho_after).max()),'max_non_pssm_endpoint_difference':float(abs(non_pssm.mean_last_minus_first_before-non_pssm.mean_last_minus_first_after).max()),'endpoint_counts_unchanged':True,'current_primary_contrasts':json.loads(new_contrast.to_json(orient='records'))})
 if axis==3:
  e=new_contrast.query("score=='am' and first=='depth0' and last=='depth4'").iloc[0]
  assert e.paired_assays==e.paired_proteins==1 and np.isnan(e.ci_low) and np.isnan(e.ci_high)
  assert e.ci_status=='insufficient_independent_proteins'
  assert 'Insufficient independent replication' in (output/'execution.log').read_text()
 add(f'axis-{axis} counts, estimands and endpoint reconstruction',f'{len(curves)} curve rows; all eligible assay/protein/variant counts preserved. AM/BLOSUM point estimates agree with previous displayed values within 5.1e-7.')
# Axes 1 and 2 use separate clinical gene/protein bootstrap logic with many clusters.
for a in [1,2]:
 nb=json.loads((R/f'inline/alphamissense/am-primary/axis-{a}.ipynb').read_text());counts=[]
 for c in nb['cells']:
  for o in c.get('outputs',[]):
   if 'text/html' in o.get('data',{}):
    for t in pd.read_html(StringIO(''.join(o['data']['text/html']))):
     if 'clusters' in t.columns:counts.extend(t.clusters.astype(int))
 assert counts and min(counts)>2
 add(f'axis-{a} clinical bootstrap inspection',{'minimum_cluster_count':min(counts),'scientific_cells_changed':False})
(HERE/'verification.json').write_text(json.dumps({'scope':'Independent helper tests and recomputation from actual per-assay records after the selected-cell rerun. No inference, fresh alignment or historical chronology claim.','checks':checks,'before_after':comparison},indent=2,allow_nan=False)+'\n')
print(f'{len(checks)} independent checks completed; fixed one-protein endpoint has no CI and no general positive claim.')
