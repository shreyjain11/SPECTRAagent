"""Independent covariance and estimand checks for corrected STATE regressions."""
import argparse,ast,gzip,hashlib,json,subprocess,warnings
from pathlib import Path
import numpy as np,pandas as pd
import statsmodels.api as sm
from scipy.stats import t
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
BASE='1d3b45baa344751b4c34ea825479c0f39b09ec21'
def definitions(source,name):
 tree=ast.parse(source);node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
 return ast.get_source_segment(source,node)
def check(test,work):
 path=ROOT/f'inline/state/state-featured/test-{test:02d}.ipynb';book=json.loads(path.read_text())
 snapshot=HERE.parent/'records'/f'state-featured-test-{test:02d}.original.ipynb.gz'
 old=json.loads(gzip.decompress(snapshot.read_bytes())) if snapshot.exists() else json.loads(subprocess.check_output(['git','show',f'{BASE}:reproduction/{path.relative_to(ROOT)}'],cwd=ROOT.parent))
 primary=test in (5,9,10)
 feature='reactome_pathway_train_support_log_mean' if primary else 'support_norm_log_mean'
 count='reactome_pathway_count' if primary else 'feature_count'
 columns=['gene_symbol_canonical','context','representation','spectra_subset','overlap_at_N',feature,count,'de_nsig_counts_real']
 inputs=HERE/'inputs';inputs.mkdir(exist_ok=True);destination=inputs/f'test-{test:02d}.csv.gz'
 if work is None:
  data=pd.read_csv(destination,low_memory=False)[columns]
 else:
  frame=pd.read_csv(work/f'test-{test:02d}/state_primary_outputs/test-{test:02d}/per_condition_results.csv',low_memory=False)
  if not primary:frame=frame[frame.spectra_subset.ne('zeroshot_cross_protocol_confirmation')].copy()
  data=frame[columns].copy();data.to_csv(destination,index=False,compression={'method':'gzip','mtime':0})
 results=[]
 for adjust in ([False,True] if primary else [True]):
  namespace={'np':np,'pd':pd,'json':json,'c_SUPPORT_COL':feature,'m_TARGET_METRIC':'overlap_at_N'}
  source=''.join(book['cells'][19 if primary else 15]['source']);name='c_standardized_ols' if primary else 'm_clustered_support_fit'
  exec(definitions(source,name),namespace)
  with warnings.catch_warnings(record=True) as new_warnings:
   warnings.simplefilter('always')
   corrected=namespace[name](data,'overlap_at_N',adjust)
  assert not new_warnings, [str(w.message) for w in new_warnings]
  coefficient=corrected['coefficients'][1]
  orig_source=''.join(old['cells'][19 if primary else 15]['source']);orig_name='c_standardized_ols' if primary else 'm_ols_support_coef'
  old_ns={'np':np,'pd':pd,'c_SUPPORT_COL':feature,'m_TARGET_METRIC':'overlap_at_N'}
  exec(definitions(orig_source,orig_name),old_ns)
  previous=old_ns[orig_name](data,'overlap_at_N',adjust) if primary else old_ns[orig_name](data)
  previous_coefficient=previous['coefficients'][1]['coef'] if primary else previous['coef']
  np.testing.assert_allclose(coefficient['coef'],previous_coefficient,rtol=0,atol=1e-12)
  w=data[data[count].gt(0)].dropna().copy()
  continuous=[feature,count]+(['de_nsig_counts_real'] if adjust else [])
  x=pd.DataFrame(index=w.index)
  for col in continuous:
   v=np.log1p(w[col]) if col=='de_nsig_counts_real' else w[col];x[col]=(v-v.mean())/v.std(ddof=0)
  x=pd.concat([x,pd.get_dummies(w[['context','representation']],drop_first=True,dtype=float)],axis=1)
  x=sm.add_constant(x).astype(float);groups=w.gene_symbol_canonical
  independent=sm.OLS(w.overlap_at_N,x).fit(cov_type='cluster',cov_kwds={'groups':groups,'use_correction':True},use_t=True)
  np.testing.assert_allclose(coefficient['coef'],independent.params[feature],rtol=0,atol=1e-12)
  np.testing.assert_allclose(coefficient['se'],independent.bse[feature],rtol=1e-10,atol=1e-12)
  np.testing.assert_allclose([coefficient['ci_low'],coefficient['ci_high']],independent.conf_int().loc[feature],rtol=1e-10,atol=1e-12)
  duplicate=namespace[name](pd.concat([data,data],ignore_index=True),'overlap_at_N',adjust)['coefficients'][1]
  assert duplicate['n_gene_clusters']==coefficient['n_gene_clusters']
  assert abs(duplicate['se']/coefficient['se']-1)<.001
  results.append({'analysis_id':f'state-featured/test-{test:02d}','adjust_de_count':adjust,'n_rows':corrected['n_rows'],'input_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'previous_coef':previous_coefficient,**coefficient,'independent_statsmodels_se':float(independent.bse[feature]),'duplicated_rows_se_ratio':duplicate['se']/coefficient['se']})
 return results
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--run-directory',type=Path,help='Optional new full-notebook run directory; defaults to the included regression tables.');args=parser.parse_args()
 rows=[]
 for test in [5,9,10,13,14,15,16,17,18,19]:
  with warnings.catch_warnings(record=True) as reference_warnings:
   warnings.simplefilter('always')
   checked=check(test,args.run_directory)
  for row in checked:
   row['corrected_function_runtime_warnings']=0
   row['reference_backend_warning_count']=len(reference_warnings)
   row['reference_backend_warning_messages']=sorted({str(w.message) for w in reference_warnings})
  rows+=checked
 (HERE/'regression-verification.json').write_text(json.dumps(rows,indent=2)+'\n')
 print(pd.DataFrame(rows)[['analysis_id','adjust_de_count','coef','ci_low','ci_high','n_gene_clusters']].to_string(index=False))
