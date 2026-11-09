"""Transparent numerical helpers for the reconstructed original investigations."""
import hashlib,json,platform,time
from pathlib import Path
import numpy as np
import pandas as pd

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def dump(path,obj):
    p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,indent=2,default=lambda x:x.item() if isinstance(x,np.generic) else str(x),allow_nan=False)+'\n')
def zscore(x):
    x=np.asarray(x,dtype=float);s=x.std(ddof=0)
    if not s>0:raise ValueError('Constant predictor')
    return (x-x.mean())/s
def fisher(x):return np.arctanh(np.clip(np.asarray(x,float),-1+1e-7,1-1e-7))
def cluster_fit(d,y,x,cluster,adjust=(),fixed=(),cluster_fixed=False,draws=10000,seed=20260715):
    """OLS and paired cluster-resampling percentile CI via exact sufficient stats.

    When cluster_fixed=True, first remove the cluster mean. Resampling duplicated
    clusters is equivalent to giving that cluster an integer frequency weight.
    Axis standardization is fixed on the original analyzed rows, not redefined
    within each bootstrap draw. No historical estimates enter this function.
    """
    cols=[y,x,cluster,*adjust,*fixed];d=d.dropna(subset=cols).copy()
    X=[np.ones(len(d)),zscore(d[x])];names=['intercept',x]
    for c in adjust:
        v=np.asarray(d[c],float)
        if np.std(v)>0:X.append(zscore(v));names.append(c)
    for c in fixed:
        for val in sorted(d[c].unique())[1:]:X.append((d[c]==val).astype(float).values);names.append(f'{c}={val}')
    X=np.column_stack(X);Y=d[y].to_numpy(float)
    groups=sorted(d[cluster].unique());codes=pd.Categorical(d[cluster],categories=groups).codes
    if cluster_fixed:
        for j in range(len(groups)):
            sel=codes==j;X[sel]-=X[sel].mean(axis=0);Y[sel]-=Y[sel].mean()
        X=X[:,1:];names=names[1:];axis_idx=0
    else:axis_idx=1
    gxx=np.zeros((len(groups),X.shape[1],X.shape[1]));gxy=np.zeros((len(groups),X.shape[1]))
    for j in range(len(groups)):
        sel=codes==j;gxx[j]=X[sel].T@X[sel];gxy[j]=X[sel].T@Y[sel]
    coefficient=np.linalg.lstsq(X,Y,rcond=None)[0];rng=np.random.default_rng(seed);boot=[]
    for start in range(0,draws,100):
        n=min(100,draws-start);w=rng.multinomial(len(groups),np.full(len(groups),1/len(groups)),size=n)
        xx=np.einsum('bg,gij->bij',w,gxx);xy=w@gxy
        for a,b in zip(xx,xy):boot.append(np.linalg.lstsq(a,b,rcond=None)[0][axis_idx])
    return dict(n=len(d),clusters=len(groups),coefficient=float(coefficient[axis_idx]),ci95=np.quantile(boot,[.025,.975]).tolist(),draws=draws,seed=seed,design_columns=names,cluster_fixed_effect=cluster_fixed,axis_standardization='population SD on all analyzed rows',coefficients=dict(zip(names,coefficient))),np.asarray(boot)
def curve(d,level,score,cluster,draws=10000,seed=20260715):
    groups=sorted(d[cluster].unique());levels=sorted(d[level].unique());rng=np.random.default_rng(seed)
    w=rng.multinomial(len(groups),np.full(len(groups),1/len(groups)),size=draws);rows=[];boot={}
    for v in levels:
        q=d[d[level]==v];g=q.groupby(cluster)[score].agg(['sum','count']).reindex(groups,fill_value=0)
        b=(w@g['sum'].values)/(w@g['count'].values);boot[str(v)]=b
        rows.append(dict(level=v,n=len(q),clusters=q[cluster].nunique(),mean=q[score].mean(),ci_low=np.quantile(b,.025),ci_high=np.quantile(b,.975)))
    return pd.DataFrame(rows),boot
def save_receipt(root,name,sources,outputs,checks,assumptions=()):
    root=Path(root);rows=[]
    for p in sources:
        p=Path(p);rows.append(dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=sha(p)))
    out=[]
    for p in outputs:
        p=Path(p);out.append(dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=sha(p)))
    dump(root/'computed'/f'{name}_receipt.json',dict(status='computed_from_public_inputs',scientific_execution_host=platform.node(),completed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),sources=rows,methods={str(p.relative_to(root)):sha(p) for p in sorted((root/'methods').glob('*.py'))},outputs=out,checks=checks,documented_assumptions=list(assumptions),historical_outputs_used_as_calculation_inputs=False))
def checked(root,rel):
    root=Path(root);p=root/'inputs'/rel;m=json.loads((root/'methods/sources.json').read_text())
    x=next(x for x in m['inputs'] if x['path']==rel)
    if p.stat().st_size!=x['bytes'] or sha(p)!=x['sha256']:raise ValueError(f'Input checksum mismatch: {rel}')
    return p
