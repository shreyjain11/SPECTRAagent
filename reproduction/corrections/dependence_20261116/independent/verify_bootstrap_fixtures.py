"""Independent fixtures for the protein-block helpers; no benchmark inference."""
import ast,itertools,json,pathlib,datetime
import numpy as np
import pandas as pd
from scipy.stats import spearmanr,rankdata
P=pathlib.Path(__file__).resolve().parent
SOURCE=P.parent/'alphamissense'
ns={'np':np,'pd':pd,'spearmanr':spearmanr,'CLUSTER_BOOTSTRAP_DRAWS':10000,'CLUSTER_SEED':20261116,'SIGN_FLIP_DRAWS':50000,'DEPTH_BOOTSTRAP_DRAWS':10000,'DEPTH_SEED':20261116}
for file in ['cluster_mean_cell.py','depth_cell.py']:
 tree=ast.parse((SOURCE/file).read_text());funs=[n for n in tree.body if isinstance(n,ast.FunctionDef)]
 exec(compile(ast.Module(body=funs,type_ignores=[]),str(SOURCE/file),'exec'),ns)
values=np.array([1.0,3.0,2.0,-.4,.1,.2]);proteins=np.array(['A','A','A','B','C','C']);rng=np.random.default_rng(20261116)
expected=[]
for row in rng.integers(0,3,size=(10000,3)):
 duplicated=np.concatenate([values[proteins==key] for key in np.array(['A','B','C'])[row]])
 expected.append(duplicated.mean())
point,lo,hi,n,g=ns['protein_bootstrap_mean'](values,proteins)
assert (n,g)==(6,3) and point==values.mean()
assert np.allclose([lo,hi],np.quantile(expected,[.025,.975]),rtol=0,atol=1e-14)
assert not np.isclose(point,pd.DataFrame({'v':values,'g':proteins}).groupby('g').v.mean().mean())
expected_p=np.mean([abs(sum(v*sign[ord(g)-65] for v,g in zip(values,proteins)))>=abs(values.sum())-1e-12 for sign in itertools.product([-1,1],repeat=3)])
p,label=ns['protein_sign_flip'](values,proteins)
assert p==expected_p and label.startswith('exact')
single=ns['protein_bootstrap_mean']([1,2,3],['A','A','A']);single_test=ns['protein_sign_flip']([1,2,3],['A','A','A'])
assert np.isnan(single[1]) and np.isnan(single[2]) and single[4]==1 and np.isnan(single_test[0])
frame=pd.DataFrame({'acc':['A','A','A','B','C','C'],'depth':[1,1,1,2,2,2],'agreement':[.2,.4,.1,.8,.5,.6]})
expected=[];rng=np.random.default_rng(20261116)
for row in rng.integers(0,3,size=(10000,3)):
 d=pd.concat([frame[frame.acc==x] for x in np.array(['A','B','C'])[row]],ignore_index=True)
 if d.depth.nunique()>1 and d.agreement.nunique()>1:
  xr=rankdata(d.depth);yr=rankdata(d.agreement);xr-=xr.mean();yr-=yr.mean()
  expected.append(float(np.sum(xr*yr)/np.sqrt(np.sum(xr*xr)*np.sum(yr*yr))))
got=ns['protein_bootstrap_spearman'](frame)
assert got['valid_bootstrap_draws']==len(expected)
# This fixture intentionally has >5% undefined draws: the helper correctly withholds its interval.
assert len(expected)<9500 and np.isnan(got['low']) and np.isnan(got['high'])
report={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':['Unequal protein block sizes preserve the assay-weighted mean and 10000-draw percentile interval.','Exact protein-block sign-flip p-value agrees with independent itertools enumeration.','A single protein gives descriptive mean but no population interval or test.','Tied depth values use reranked expanded rows; valid draw count independently matches; >5% degenerate draws correctly withhold the interval.'],'fixtures_only':True,'issues':[]}
(P/'protein-helper-fixtures.json').write_text(json.dumps(report,indent=2)+'\n')
print('4 independent fixture checks passed')
