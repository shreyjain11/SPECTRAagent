"""Small independent numerical checks; run on the authorized execution host."""
from pathlib import Path
import numpy as np
import pandas as pd
from common import cluster_fit,zscore,dump

def main():
    rng=np.random.default_rng(303);g=np.repeat(np.arange(12),6);c=np.tile(np.repeat(['a','b','c'],2),12);x=rng.normal(size=len(g));v=rng.normal(size=len(g));y=.3*x-.4*v+g/10+rng.normal(size=len(g))/5
    d=pd.DataFrame(dict(g=g,c=c,x=x,v=v,y=y));fit,_=cluster_fit(d,'y','x','g',adjust=['v'],fixed=['c'],cluster_fixed=True,draws=50,seed=99)
    full=np.column_stack([np.ones(len(g)),zscore(x),zscore(v),pd.get_dummies(c,drop_first=True,dtype=float),pd.get_dummies(g,drop_first=True,dtype=float)])
    expected=np.linalg.lstsq(full,y,rcond=None)[0][1];assert abs(fit['coefficient']-expected)<1e-12
    pooled,_=cluster_fit(d,'y','x','g',adjust=['v'],fixed=['c'],draws=50,seed=99)
    design=full[:,:5];expected2=np.linalg.lstsq(design,y,rcond=None)[0][1];assert abs(pooled['coefficient']-expected2)<1e-12
    # Exact complete-case behavior: a missing control removes only that row.
    d.loc[0,'v']=np.nan;complete,_=cluster_fit(d,'y','x','g',adjust=['v'],draws=50,seed=99);assert complete['n']==len(d)-1
    result=dict(passed=True,checks=['within-cluster fit equals explicit cluster-dummy OLS','pooled fit equals direct OLS','control missingness defines complete cases'],max_absolute_error=max(abs(fit['coefficient']-expected),abs(pooled['coefficient']-expected2)))
    dump(Path(__file__).resolve().parent/'SOFTWARE_TEST_RECEIPT.json',result);print(result)
if __name__=='__main__':main()
