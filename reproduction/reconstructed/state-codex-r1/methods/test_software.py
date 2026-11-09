"""Software-only synthetic fixtures. Not recovered STATE data or scientific validation."""
import inspect,json,sys,tempfile,platform
from pathlib import Path
import numpy as np,pandas as pd,statsmodels,statsmodels.api as sm,pyarrow,scipy
import reconstruct as r
base=Path(__file__).resolve().parent
m=r.original_scoring();checks=[]
def ok(name):checks.append({'check':name,'passed':True,'input_kind':'synthetic software fixture'})
with tempfile.TemporaryDirectory(dir=base,prefix='synthetic-tests-') as td:
 p=Path(td);rows=[];all_expected=[];counts=[]
 for ci,(cell,stem) in enumerate(m.CONTEXT_FILES.items()):
  real=[];pred=[];released=[]
  for ji,name in enumerate(['a','b','c','d','e','f','g','h','i','j']):
   for di,dose in enumerate([.05,.5]):
    target=repr([(name,dose,'uM')]);obs=np.array([.2,.7,1.2])*(1+.07*ji+.11*ci)+.03*di
    err=np.array([-.1,.25,.4])*(1+.3*ci)+ji*.02
    for k in range(3):
     real.append({'target':target,'feature':f'g{k}','fold_change':2**obs[k],'fdr':.01 if k==0 else .7})
     pred.append({'target':target,'feature':f'g{k}','fold_change':2**(obs[k]+err[k])})
    released.append({'perturbation':target});cnt=20+ji*3+ci
    counts.append({'target':target,'cell_line':cell,'n_cells_full':0 if ji==0 else cnt,'n_cells_all':cnt+4})
    all_expected.append({'target':target,'cell_line':cell,'expected_state':float(np.sqrt(np.mean(err**2))),'expected_identity':float(np.sqrt(np.mean(obs**2)))})
  pd.DataFrame(real).to_csv(p/f'{stem}_real_de.csv',index=False);pd.DataFrame(pred).to_csv(p/f'{stem}_pred_de.csv',index=False);pd.DataFrame(released).to_csv(p/f'{stem}_results.csv',index=False)
 axis=pd.DataFrame({'cell_line':r.CONTEXTS,'axis_value':[1.,2.,4.,6.,8.]})
 conditions,eligibility,allrows=r.build_condition_table(p,p,pd.DataFrame(counts),axis,axis_z_scope='all_rows')
 expected=conditions.merge(pd.DataFrame(all_expected),on=['cell_line','target'],validate='one_to_one')
 np.testing.assert_allclose(expected.state_lfc_rmse,expected.expected_state,atol=1e-14)
 np.testing.assert_allclose(expected.identity_lfc_rmse,expected.expected_identity,atol=1e-14)
 assert (expected.n_de==1).all() and (expected.n_genes_lfc==3).all()
 ok('Official-DE log2 RMSE and zero-effect reference agree with independent analytic arithmetic')
 assert len(conditions)==100 and len(eligibility)==10
 assert (conditions.loc[conditions.compound=='a','n_cells']==conditions.loc[conditions.compound=='a','n_cells_all']).all()
 assert all(conditions.groupby('compound').partition.nunique()==1)
 ok('Five-context eligibility, compound SHA partition and zero-full-QC fallback')
 # Independent explicit target fixed-effects regression versus original within transform.
 c=conditions.loc[conditions.partition=='confirmation'].copy(); names=['distance_z',*r.CONTROLS]
 x=c[names].copy()
 for col in r.CONTROLS:
  sd=x[col].std(ddof=1)
  if sd>0:x[col]=(x[col]-x[col].mean())/sd
 full=pd.concat([x.reset_index(drop=True),pd.get_dummies(c.target.reset_index(drop=True),dtype=float)],axis=1)
 fit=sm.OLS(c.state_lfc_rmse.to_numpy(),full.to_numpy()).fit()
 np.testing.assert_allclose(m.fit_within(c,'state_lfc_rmse',r.CONTROLS)['estimate'],fit.params[0],atol=2e-11)
 ok('Original within-target coefficient equals independent explicit target-fixed-effects OLS')
 result,spc=r.analyze_axis(conditions,seed=734,reps=31)
 np.testing.assert_allclose(result['models']['state_adjusted']['estimate'],m.fit_within(c,'state_lfc_rmse',r.CONTROLS)['estimate'],atol=1e-14)
 ok('Reconstructed analysis point estimates use surviving original fit function')
 twin=conditions.copy();twin['state_lfc_rmse']=twin.identity_lfc_rmse
 paired,_=r.analyze_axis(twin,seed=734,reps=31)
 np.testing.assert_allclose(paired['paired_state_minus_identity']['ci95'],[0,0],atol=0)
 np.testing.assert_allclose(paired['paired_state_minus_identity']['estimate'],0,atol=0)
 ok('Paired bootstrap identical-outcome invariant gives exactly zero difference and interval')
 a=m.bootstrap_slope(c,'state_lfc_rmse',[],31,734);b=m.bootstrap_slope(c,'identity_lfc_rmse',[],31,734)
 np.testing.assert_allclose(result['paired_state_minus_identity']['ci95'],np.quantile(a-b,[.025,.975]),atol=0)
 ok('Reference contrast uses exactly shared original compound-bootstrap multiplicities')
 for cov in [[],r.CONTROLS]:
  fast=r.bootstrap_slopes_fast(c,'state_lfc_rmse',cov,reps=1027,seed=927,batch_size=128)
  reference=m.bootstrap_slope(c,'state_lfc_rmse',cov,1027,927)
  np.testing.assert_allclose(fast,reference,rtol=2e-8,atol=2e-10)
 ok('Batched bootstrap matches original scalar least-squares draws across batch boundaries')
 matching,matched,strata=r.quintile_matching(c)
 wanted=[f'{prefix}_{i}' for prefix in ['effect_q','cells_q'] for i in range(1,5)]
 assert matching['controls']==wanted and len(matched)==len(c)
 assert all(name in matched for name in wanted)
 assert set(matched.target)==set(c.target)
 # Independent target-fixed-effects fit with the recovered eight indicator controls.
 design=matched[['distance_z',*wanted]].copy()
 for column in wanted:
  sd=design[column].std(ddof=1)
  if sd>0:design[column]=(design[column]-design[column].mean())/sd
 full=pd.concat([design.reset_index(drop=True),pd.get_dummies(matched.target.reset_index(drop=True),dtype=float)],axis=1)
 direct=sm.OLS(matched.state_lfc_rmse.to_numpy(),full.to_numpy()).fit()
 np.testing.assert_allclose(matching['estimate'],direct.params[0],atol=1e-10)
 ok('Recovered quintile indicator adjustment keeps all rows and matches explicit target-fixed-effects OLS')
 # An intentionally unbalanced-doses fixture distinguishes compound weighting from row weighting.
 z=pd.DataFrame({'compound':['one','two','two','two'],'cell_line':['X']*4,'state_lfc_rmse':[0,2,4,6],'identity_lfc_rmse':[0,2,4,6],'distance':[1]*4,'ccle_distance':[1]*4,'target':['a','b','c','d']})
 table=m.context_spc(z,17,734);assert table.state_rmse_mean.iloc[0]==2 and z.state_lfc_rmse.mean()==3
 ok('SPC balances compounds after dose averaging instead of weighting every condition equally')
 for fn,args in [(r.analyze_axis,(conditions,)),(r.build_condition_table,(p,p,pd.DataFrame(counts),axis))]:
  try:fn(*args)
  except TypeError:pass
  else:raise AssertionError('Unresolved methodological arguments silently defaulted')
 ok('Unrecovered seed/repetitions and axis-z scope cannot silently default')
 try:r.build_condition_table(p,p,pd.DataFrame(counts),axis,axis_z_scope='choose-to-fit')
 except ValueError:pass
 else:raise AssertionError('Invalid z scope accepted')
 ok('Unsupported standardization policy rejected')
 # Input-side feature construction independent of results.
 obs=[]
 for ci,cell in enumerate(r.CONTEXTS):
  for j in range(6):obs.append({'cell_name':cell,'drug':'DMSO_TF','plate':f'plate{j+1}','S_score':(ci+1)*(.1+j*.03),'pass_filter':'full' if j<4 else 'other'})
  obs.append({'cell_name':cell,'drug':'treated','plate':'plate1','S_score':100000.,'pass_filter':'full'})
 pd.DataFrame(obs).to_parquet(p/'synthetic_obs.parquet')
 feats=r.s_phase_features(p/'synthetic_obs.parquet');allf=feats[feats.subset=='all'].set_index('cell_line')
 np.testing.assert_allclose(allf.axis_value,[np.std(np.arange(6)*.03*(ci+1),ddof=1) for ci in range(5)],atol=1e-14)
 assert (allf.n_baseline_cells==6).all();assert(feats[feats.subset=='full'].n_baseline_cells==4).all()
 ok('S-phase uses sample SD of untreated cells and separates full-QC/plate sensitivities')
 mapping=pd.DataFrame([{'cell_line':cell,'depmap_id':str(i),'lineage':'L'+str(i%2)} for i,cell in enumerate(r.CONTEXTS)]+[{'cell_line':'train'+str(i),'depmap_id':'tr'+str(i),'lineage':'L'+str(i%2)} for i in range(7)])
 lineage=r.lineage_features(mapping);np.testing.assert_allclose(lineage.axis_value,-np.log1p([4,3,4,3,4]));assert lineage.axis_level.nunique()==2
 ok('Lineage counts exclude held-out contexts and preserve tied lineage levels')
receipt={'purpose':'software validation only; no scientific data or result reproduction','scientific_workflow_executed':False,'method_source_sha256':{name:__import__('hashlib').sha256((base/name).read_bytes()).hexdigest() for name in ['reconstruct.py','test_software.py','original/04_analyze_frozen_axis.py']},'fixture_origin':'generated in this file; temporary files removed','python':platform.python_version(),'versions':{'numpy':np.__version__,'pandas':pd.__version__,'scipy':scipy.__version__,'statsmodels':statsmodels.__version__,'pyarrow':pyarrow.__version__},'checks':checks,'passed':len(checks)}
(base/'SOFTWARE_TEST_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
