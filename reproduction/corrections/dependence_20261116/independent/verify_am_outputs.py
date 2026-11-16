"""Numerical checks from persisted assay/control rows, independent of notebook helpers."""
import datetime,hashlib,itertools,json,pathlib,sys,warnings
import numpy as np
import pandas as pd
from scipy.stats import rankdata
import statsmodels.api as sm
HERE=pathlib.Path(__file__).resolve().parent
DATA=HERE.parent/'alphamissense/outputs'
B=10000;SEED=20261116

def same(a,b,tol=2e-12):
 assert np.allclose(np.asarray(a,dtype=float),np.asarray(b,dtype=float),atol=tol,rtol=0,equal_nan=True),(a,b)

def cluster_mean(v,p):
 v=np.asarray(v,float);p=np.asarray(p);finite=np.isfinite(v);v=v[finite];p=p[finite]
 keys=sorted(set(p));G=len(keys)
 if len(v)==0:return (np.nan,np.nan,np.nan,0,0)
 if G<2:return (v.mean(),np.nan,np.nan,len(v),G)
 # Each original assay row receives its accession's draw multiplicity.
 inv=np.array([keys.index(g) for g in p]);sample=np.random.default_rng(SEED).integers(G,size=(B,G))
 counts=np.zeros((B,G),dtype=np.int64);np.add.at(counts,(np.repeat(np.arange(B),G),sample.ravel()),1)
 weights=counts[:,inv];means=np.sum(weights*v[None,:],axis=1)/weights.sum(axis=1)
 for draw in range(5):
  expanded=np.concatenate([v[p==keys[j]] for j in sample[draw]])
  same(expanded.mean(),means[draw])
 lo,hi=np.quantile(means,[.025,.975]);return(v.mean(),lo,hi,len(v),G)

def sign_flip(v,p):
 v=np.asarray(v,float);p=np.asarray(p);finite=np.isfinite(v);v=v[finite];p=p[finite];keys=sorted(set(p));G=len(keys)
 if G<2:return np.nan
 block_sums=np.array([v[p==g].sum() for g in keys]);obs=abs(v.sum());tol=32*np.finfo(float).eps*max(1,abs(block_sums).sum())
 if G<=16:
  # Enumerate signs without the implementation's bit-matrix construction.
  vals=[abs(sum(s*z for s,z in zip(sign,block_sums))) for sign in itertools.product([-1,1],repeat=G)]
  return np.mean(np.asarray(vals)>=obs-tol)
 signs=2*np.random.default_rng(SEED).integers(0,2,size=(50000,G),dtype=np.int8)-1
 # Apply each protein's sign to original assay rows, then sum assays.
 inv=np.array([keys.index(g) for g in p]);null=abs(np.sum(signs[:,inv]*v[None,:],axis=1))
 return (int(np.sum(null>=obs-tol))+1)/50001

def spearman(x,y):
 x=rankdata(x);y=rankdata(y);x-=x.mean();y-=y.mean();den=np.sqrt(np.sum(x*x)*np.sum(y*y))
 return np.sum(x*y)/den if den>0 else np.nan

def depth_check(folder):
 table=pd.read_csv(folder/'assay_performance.csv');output=pd.read_csv(folder/'depth_controls.csv');results=[]
 assert table.groupby('assay').acc.nunique().eq(1).all() and table.groupby('acc').split.nunique().eq(1).all()
 subsets={'All':table,'Excluding stability':table[table.selection!='Stability'],'Stability only':table[table.selection=='Stability'],'Discovery':table[table.split=='discovery'],'Confirmation':table[table.split=='confirmation']}
 for _,row in output.iterrows():
  d=subsets[row['subset']].reset_index(drop=True);keys=sorted(d.acc.unique());G=len(keys);x=d.depth.to_numpy();y=d.agreement.to_numpy();blocks=[np.flatnonzero(d.acc==g) for g in keys]
  same(spearman(x,y),row.rho);assert len(d)==row.n_assays and G==row.n_proteins
  draws=np.random.default_rng(SEED).integers(G,size=(B,G));samples=[]
  for draw in draws:
   idx=np.concatenate([blocks[j] for j in draw]);value=spearman(x[idx],y[idx])
   if np.isfinite(value):samples.append(value)
  assert len(samples)==row.valid_bootstrap_draws
  ci=np.quantile(samples,[.025,.975]) if len(samples)>=.95*B else [np.nan,np.nan]
  same(ci,[row.low,row.high]);results.append({'subset':row['subset'],'n_assays':len(d),'n_proteins':G,'rho':float(row.rho),'ci95':[float(row.low),float(row.high)],'independent_draws_checked':B})
 assert 'p' not in output.columns
 return {'depth':results,'split_protein_disjoint':True}

def regression_check(folder):
 output=pd.read_csv(folder/'adjusted_controls.csv');checks=[]
 for binning in ['coverage','plddt']:
  table=pd.read_csv(folder/f'control_cells_{binning}.csv');cols=['coverage','plddt','log_dms_sd'];features=table[cols]
  # Fit the equivalent explicit assay fixed-effect model to uncentered outcomes.
  design=pd.concat([pd.get_dummies(table.assay,dtype=float),features],axis=1)
  with warnings.catch_warnings(record=True) as caught:
   fit=sm.OLS(table.am,design).fit(cov_type='cluster',cov_kwds={'groups':table.acc,'use_correction':True},use_t=True)
  target=output[output.binning==binning].set_index('covariate').loc[cols]
  same(fit.params.loc[cols],target.beta);same(fit.bse.loc[cols],target.standard_error)
  same(fit.conf_int().loc[cols].to_numpy(),target[['ci_low','ci_high']].to_numpy())
  same(fit.pvalues.loc[cols],target.p_two_sided)
  assert (target.effective_parameter_rank==np.linalg.matrix_rank(design)).all()
  assert (target.n_proteins==table.acc.nunique()).all()
  checks.append({'binning':binning,'assays':int(table.assay.nunique()),'proteins':int(table.acc.nunique()),'rows':len(table),'effective_design_rank':int(np.linalg.matrix_rank(design)),'max_coefficient_difference':float(np.max(abs(fit.params.loc[cols]-target.beta))),'max_standard_error_difference':float(np.max(abs(fit.bse.loc[cols]-target.standard_error))),'warnings':[str(w.message) for w in caught]})
 return checks

def curve_check(folder):
 scores=pd.read_csv(folder/'assay_level_scores.csv');curves=pd.read_csv(folder/'curves.csv');effects=pd.read_csv(folder/'paired_effects.csv')
 assert scores.groupby('assay').acc.nunique().eq(1).all() and scores.groupby('acc').split.nunique().eq(1).all()
 for _,row in curves.iterrows():
  cell=scores[(scores.scheme==row.scheme)&(scores.level==row.level)];values=cell[row.method]
  mean,lo,hi,n,g=cluster_mean(values,cell.acc);same([mean,lo,hi],[row['mean'],row.low,row.high]);assert(n,g)==(row.n_assays,row.n_proteins)
 results=[]
 for (label,scheme),out in effects.groupby(['subset','scheme']):
  group=scores[scores.scheme==scheme].copy()
  if label=='Discovery':group=group[group.split=='discovery']
  elif label=='Confirmation':group=group[group.split=='confirmation']
  elif label=='Excluding stability':group=group[group.selection!='Stability']
  elif label=='At least 30 homologs':group=group[group.total_hits>=30]
  else:assert label=='All'
  levels=scores.loc[scores.scheme==scheme,'level'];lo,hi=levels.min(),levels.max()
  pivots={name:group.pivot(index='assay',columns='level',values=name).reindex(columns=[lo,hi]) for name in ['AM','BLOSUM','PSSM']}
  ids=sorted(set.intersection(*[set(p.dropna().index) for p in pivots.values()]))
  proteins=group[['assay','acc']].drop_duplicates().set_index('assay').loc[ids,'acc'].to_numpy()
  contrasts={name:p.loc[ids,hi].to_numpy()-p.loc[ids,lo].to_numpy() for name,p in pivots.items()}
  contrasts['AM minus BLOSUM']=contrasts['AM']-contrasts['BLOSUM'];contrasts['AM minus PSSM']=contrasts['AM']-contrasts['PSSM']
  for _,row in out.iterrows():
   value=contrasts[row.comparison];mean,l,h,n,g=cluster_mean(value,proteins)
   same([mean,l,h],[row['mean'],row.low,row.high]);assert(n,g)==(row.n_assays,row.n_proteins)
   same(sign_flip(value,proteins),row.sign_flip_p,tol=1e-15)
   if label=='All' and row.comparison=='AM':results.append({'scheme':scheme,'mean':float(mean),'ci95':[float(l),float(h)],'assays':n,'proteins':g})
 assert 'wilcoxon_p' not in effects.columns
 return {'curve_points':len(curves),'paired_comparisons':len(effects),'bootstrap_draws_per_statistic':B,'all_cluster_intervals_counts_and_sign_flip_tests_reproduced':True,'split_protein_disjoint':True,'pooled_AM_effects':results}

wanted=sys.argv[1:];folders=[DATA/x for x in wanted] if wanted else sorted(DATA.glob('am-opus-r*-test-*'))
reports=[]
for folder in folders:
 if not(folder/'CURRENT_RESULTS.json').exists():continue
 if(folder/'depth_controls.csv').exists():detail=depth_check(folder)
 else:
  detail=curve_check(folder)
  if(folder/'adjusted_controls.csv').exists():detail['adjusted_controls']=regression_check(folder)
 d={'analysis_id':folder.name,'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'method':'Independently compute statistics from exported individual assay/control rows. Bootstrap weights apply to original rows; sign flips independently apply to individual assay contrasts; Spearman uses independently centered tied ranks; regression uses full explicit assay dummy design in statsmodels.','files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.glob('*.csv')},'checks':detail,'issues':[]}
 (HERE/(folder.name+'-independent.json')).write_text(json.dumps(d,indent=2)+'\n');reports.append(d)
 print(folder.name,'checked',flush=True)
print('Finished',len(reports),'notebooks')
