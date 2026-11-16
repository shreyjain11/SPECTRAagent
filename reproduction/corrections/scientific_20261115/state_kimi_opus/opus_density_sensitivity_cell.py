import numpy as np, pandas as pd
from scipy.stats import spearmanr
df=pd.read_csv((WORK / 'data/predictions.csv'),low_memory=False)
r=df[df.dataset_family=='Replogle-Nadig'].copy()
feat=pd.read_csv((WORK / 'spectra_run/artifacts/replogle_go_features.csv'))
d=r.merge(feat,on='perturbation_name',how='inner')
z=d[d.protocol=='zeroshot'].copy()

# Deciles of evaluation-panel neighborhood density. D1=sparsest .. D10=densest
z['decile']=pd.qcut(z['go_meantop5'],10,labels=range(1,11))
spc=z.groupby(['representation','decile'],observed=True)['overlap_at_N'].agg(['mean','median','count']).reset_index()
spc.to_csv((WORK / 'spectra_run/artifacts/SPC_replogle_deciles.csv'),index=False)
print('=== Density curve (deciles; D1=sparsest, D10=densest) — overlap_at_N mean ===')
piv=spc.pivot(index='decile',columns='representation',values='mean').round(4)
print(piv)

# Sensitivity restricted to above-median observed DE count; not exact effect matching
z['eff_half']=(z['de_nsig_counts_real']>z['de_nsig_counts_real'].median()).map({True:'strong',False:'weak'})
print('\n=== Density sensitivity among above-median observed-DE conditions (does not remove all difficulty) ===')
for rep in ['HVG','SE']:
    zz=z[(z.representation==rep)&(z.eff_half=="strong")].copy()
    zz['q']=pd.qcut(zz['go_meantop5'],4,labels=['L1_novel','L2','L3','L4_covered'])
    m=zz.groupby('q',observed=True)['overlap_at_N'].mean()
    rho,p=spearmanr(zz['go_meantop5'],zz['overlap_at_N'])
    print(f'  {rep} (strong-effect only): rho={rho:+.3f} n={len(zz)}  L1={m["L1_novel"]:.3f} L4={m["L4_covered"]:.3f} ratio={m["L4_covered"]/m["L1_novel"]:.2f}x')

# Final headline SPC (quartiles) table saved
z['novlevel']=pd.qcut(z['go_meantop5'],4,labels=['L1_novel','L2','L3','L4_covered'])
head=z.groupby(['representation','novlevel'],observed=True)['overlap_at_N'].agg(['mean','median','std','count']).reset_index()
head.to_csv((WORK / 'spectra_run/artifacts/SPC_replogle_quartiles.csv'),index=False)
print('\nSaved SPC tables.')
