"""Numerical tests for the exact helpers copied into the six notebooks."""
from pathlib import Path
import ast,json
import numpy as np,pandas as pd
from scipy.stats import spearmanr
HERE=Path(__file__).resolve().parent
ns={'np':np,'pd':pd,'spearmanr':spearmanr}
def definitions(path):
 t=ast.parse(path.read_text())
 keep=[s for s in t.body if isinstance(s,(ast.FunctionDef,ast.Import,ast.ImportFrom)) or (isinstance(s,ast.Assign) and all(isinstance(x,ast.Name) and x.id.isupper() for x in s.targets))]
 exec(compile(ast.Module(body=keep,type_ignores=[]),str(path),'exec'),ns)
definitions(HERE/'cluster_mean_cell.py');definitions(HERE/'depth_cell.py')
tests=[]
def checked(name,condition):
 assert condition,name
 tests.append({'check':name,'verified':True})
r=ns['protein_bootstrap_mean']([0,0,9],['A','A','B'])
checked('Unequal cluster sizes retain the assay-weighted point mean3 rather than protein-weighted4.5',r[0]==3 and r[3:]==(3,2))
checked('Two-protein bootstrap includes whole A and B blocks',r[1:3]==(0.,9.))
r1=ns['protein_bootstrap_mean']([0,9],['A','A'])
checked('One-protein interval unavailable despite multiple assays',r1[0]==4.5 and np.isnan(r1[1]) and np.isnan(r1[2]) and r1[4]==1)
p,method=ns['protein_sign_flip']([1,2,3],['A','A','B'])
checked('Exact sign-flip flips both A assay contrasts together',p==.5 and method=='exact protein-block sign flip')
checked('One-protein paired test unavailable',np.isnan(ns['protein_sign_flip']([1,2],['A','A'])[0]))
checked('All-zero paired contrasts produce p1',ns['protein_sign_flip']([0,0],['A','B'])[0]==1.)
frame=pd.DataFrame({'depth':[1,2,4,6,9],'agreement':[.2,.8,.4,.5,.1],'acc':['A','A','B','C','D']})
actual=ns['protein_bootstrap_spearman'](frame,repeats=200,seed=4321)
rng=np.random.default_rng(4321);draws=[]
for block_ids in rng.integers(0,4,size=(200,4)):
 expanded=pd.concat([frame[frame.acc==['A','B','C','D'][j]] for j in block_ids],ignore_index=True)
 if expanded.depth.nunique()>1 and expanded.agreement.nunique()>1:draws.append(spearmanr(expanded.depth,expanded.agreement).statistic)
expected=np.quantile(draws,[.025,.975])
checked('Depth bootstrap equals independent expanded-block reranking',np.allclose([actual['low'],actual['high']],expected) and actual['valid_bootstrap_draws']==len(draws))
checked('Depth point estimate remains original assay-level Spearman',actual['rho']==spearmanr(frame.depth,frame.agreement).statistic)
repeat=ns['protein_bootstrap_mean']([0,0,9],['A','A','B'])
checked('Fixed-seed bootstrap deterministic',repeat==r)
(HERE/'helper-test-results.json').write_text(json.dumps({'scope':'Synthetic numerical tests of clustering/estimand mechanics; not scientific validation','tests':tests},indent=2)+'\n')
print('Verified',len(tests),'helper checks')
