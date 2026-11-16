import numpy as np, pandas as pd, json
from scipy.stats import spearmanr, rankdata

df=pd.read_csv(WORK / 'data/predictions.csv',low_memory=False)
r=df[df.dataset_family=='Replogle-Nadig'].copy()
feat=pd.read_csv(WORK / 'spectra_run/artifacts/replogle_go_features.csv')
gene_ctx=r.groupby('perturbation_name')['context'].nunique()
r['other_ctx_cov']=r['perturbation_name'].map(gene_ctx)-1
d=r.merge(feat,on='perturbation_name',how='inner',validate='many_to_one')
z=d[d.protocol=='zeroshot'].copy()

def prepare_partial(frame, x, y, continuous, categorical):
    names=[x,y,*continuous,*categorical,'perturbation_name']
    data=frame[names].dropna().copy()
    values=[data[c].to_numpy(dtype=float) for c in [x,y,*continuous]]
    # Fixed tie groups are safe: multiplicities, hence tied midranks, change per draw.
    tie_codes=[np.unique(v,return_inverse=True)[1] for v in values]
    categories=pd.get_dummies(data[categorical],drop_first=True,dtype=float) if categorical else pd.DataFrame(index=data.index)
    indicators=categories.to_numpy(dtype=float)
    genes=sorted(data.perturbation_name.unique());gene_code=pd.Categorical(data.perturbation_name,categories=genes).codes
    def statistic(weights):
        def weighted_ranks(codes):
            counts=np.bincount(codes,weights=weights)
            midranks=np.cumsum(counts)-(counts-1.0)/2.0
            return midranks[codes]
        ranks=[weighted_ranks(c) for c in tie_codes]
        design=np.column_stack([np.ones(len(data)),*ranks[2:],indicators])
        positive=weights>0; w=np.sqrt(weights[positive])
        A=design[positive]*w[:,None];Y=np.column_stack(ranks[:2])[positive]
        if np.linalg.matrix_rank(A)!=A.shape[1]:
            raise ValueError('Rank-deficient partial-rank design')
        beta=np.linalg.lstsq(A,Y*w[:,None],rcond=None)[0]
        residual=Y-np.einsum('ij,jk->ik',design[positive],beta,optimize=False)
        ww=weights[positive];residual-=np.average(residual,weights=ww,axis=0)
        covariance=np.einsum('ij,i,ik->jk',residual,ww,residual,optimize=False)
        if not np.isfinite(residual).all() or not np.isfinite(covariance).all():
            raise ValueError('Nonfinite partial-rank intermediate')
        return float(covariance[0,1]/np.sqrt(covariance[0,0]*covariance[1,1]))
    return data,genes,gene_code,statistic,list(categories.columns)

def clustered_partial(frame,x,y,continuous,categorical,seed=20261115,n_boot=10000):
    data,genes,gene_code,statistic,indicators=prepare_partial(frame,x,y,continuous,categorical)
    estimate=statistic(np.ones(len(data)))
    generator=np.random.default_rng(seed);draws=np.empty(n_boot)
    for b in range(n_boot):
        multiplicity=np.bincount(generator.integers(0,len(genes),len(genes)),minlength=len(genes))
        draws[b]=statistic(multiplicity[gene_code])
    if not np.isfinite(draws).all():raise ValueError('Nonfinite bootstrap correlation')
    result={'rho':estimate,'ci95':np.quantile(draws,[.025,.975]).tolist(),'rows':len(data),'gene_clusters':len(genes),'draws':n_boot,'seed':seed,'continuous_controls':continuous,'context_indicators':indicators,'scope':'gene-cluster bootstrap conditional on the observed contexts; ranks and residualization refitted per draw'}
    return result,draws

print('=== 1) Fixed-N metric sensitivity (descriptive correlations; no pooled-row p values) ===')
for rep in ['HVG','SE']:
    zz=z[z.representation==rep]
    for mcol in ['overlap_at_50','overlap_at_100','overlap_at_200','overlap_at_500','precision_at_100']:
        rho,p=spearmanr(zz['go_meantop5'],zz[mcol]);print(f'   {rep} {mcol:16s}: rho={rho:+.3f}')
summary={};draw_table={}
for label,continuous,categorical in [('effect_adjusted',['de_nsig_counts_real'],[]),('effect_coverage_context_adjusted',['de_nsig_counts_real','other_ctx_cov'],['context'])]:
    print('\n=== Partial rank correlation:',label,'===')
    summary[label]={}
    for rep in ['HVG','SE']:
        result,draws=clustered_partial(z[z.representation==rep],'overlap_at_N','go_meantop5',continuous,categorical)
        summary[label][rep]=result;draw_table[label+'_'+rep]=draws
        print(f"   {rep}: rho={result['rho']:+.6f}; gene-bootstrap 95% CI={result['ci95']}; genes={result['gene_clusters']}; rows={result['rows']}")
(WORK/'spectra_run/artifacts/partial_rank_gene_bootstrap_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
pd.DataFrame(draw_table).to_csv(WORK/'spectra_run/artifacts/partial_rank_gene_bootstrap_draws.csv',index=False)
print('\n=== Density versus mean observed DE count, at gene level ===')
gmean=z.groupby('perturbation_name').agg(nsig=('de_nsig_counts_real','mean'),dens=('go_meantop5','first'))
rho,p=spearmanr(gmean['dens'],gmean['nsig']);print(f'   rho={rho:+.3f}; p={p:.1e}; descriptive association, not causal mechanism')
