import json, numpy as np, pandas as pd
from scipy.stats import spearmanr
df=pd.read_csv((WORK / 'data/predictions.csv'),low_memory=False)
r=df[df.dataset_family=='Replogle-Nadig'].copy()
feat=pd.read_csv((WORK / 'spectra_run/artifacts/replogle_go_features.csv'))
go=json.load(open((WORK / 'spectra_run/artifacts/go_terms.json')))
d=r.merge(feat,on='perturbation_name',how='inner')
z=d[d.protocol=='zeroshot']

print('=== A) Per-context associations in the same benchmark (genes can recur) ===')
for rep in ['HVG','SE']:
    for ctx in sorted(z['context'].unique()):
        zz=z[(z.representation==rep)&(z.context==ctx)]
        rho,p=spearmanr(zz['go_meantop5'],zz['overlap_at_N'])
        print(f'   {rep} {ctx:7s}: rho={rho:+.3f} p={p:.1e} n={len(zz)}')
    print()

print('=== B) Density trimming sensitivity: exclude the highest-density decile ===')
# tag genes whose top GO includes ribosome/translation/proteasome/splic/mito
big_terms_keywords=None
# use CC/BP to flag ribosomal & spliceosomal etc via term presence is hard; instead exclude top-density decile
for rep in ['HVG','SE']:
    zz=z[z.representation==rep].copy()
    # exclude the densest 10% (likely core complexes) and re-test on the remaining 90%
    thr=feat['go_meantop5'].quantile(0.90)
    sub=zz[zz['go_meantop5']<thr]
    rho,p=spearmanr(sub['go_meantop5'],sub['overlap_at_N'])
    print(f'   {rep} excl top-decile density: rho={rho:+.3f} n={len(sub)}')
    # also exclude bottom decile (orphans) to test middle range
    thr2=feat['go_meantop5'].quantile(0.10)
    sub2=zz[(zz['go_meantop5']>thr2)&(zz['go_meantop5']<thr)]
    rho2,p2=spearmanr(sub2['go_meantop5'],sub2['overlap_at_N'])
    print(f'   {rep} middle 80% only    : rho={rho2:+.3f} n={len(sub2)}')

print('\n=== C) Reproducible gene-half sensitivity split (not prospective confirmation) ===')
import hashlib
salt='STATE-OPUS-R2-sensitivity-v1|'
genes=sorted(set(feat['perturbation_name'].dropna()))
split=pd.DataFrame({'gene':genes,'sha256':[hashlib.sha256((salt+g).encode('utf-8')).hexdigest() for g in genes]})
split=split.sort_values(['sha256','gene']).reset_index(drop=True)
split['half']=np.arange(len(split))%2
assert abs(int((split.half==0).sum())-int((split.half==1).sum()))<=1
split.to_csv(WORK/'spectra_run/artifacts/gene_sensitivity_split_sha256.csv',index=False)
half=dict(zip(split.gene,split.half))
print('Split salt:',salt,'gene counts:',split.half.value_counts().sort_index().to_dict())
z=z.copy(); z['half']=z['perturbation_name'].map(half)
for rep in ['HVG','SE']:
    for h in [0,1]:
        zz=z[(z.representation==rep)&(z.half==h)]
        rho,p=spearmanr(zz['go_meantop5'],zz['overlap_at_N'])
        print(f'   {rep} gene-half {h}: rho={rho:+.3f} n={len(zz)}')

print('\n=== D) Examples at the sparse and dense ends of the evaluation-gene panel ===')
feat2=feat.sort_values('go_meantop5')
print('  lowest-density evaluation genes:', feat2['perturbation_name'].head(15).tolist())
print('  highest-density evaluation genes:', feat2['perturbation_name'].tail(15).tolist())
