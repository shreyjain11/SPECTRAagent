# Preserve the across-assay Spearman coefficient; resample whole protein blocks and rerank each draw.
DEPTH_BOOTSTRAP_DRAWS=10000
DEPTH_SEED=20261116

def protein_bootstrap_spearman(table,repeats=DEPTH_BOOTSTRAP_DRAWS,seed=DEPTH_SEED):
    frame=table[['depth','agreement','acc']].replace([np.inf,-np.inf],np.nan).dropna()
    assert len(frame)==len(table), 'Existing depth eligibility must not change silently'
    proteins=sorted(frame.acc.unique());g=len(proteins)
    point=float(spearmanr(frame.depth,frame.agreement).statistic) if len(frame)>2 else np.nan
    result=dict(n_assays=len(frame),n_proteins=g,rho=point,low=np.nan,high=np.nan,valid_bootstrap_draws=0,
                interval_method='protein-block percentile bootstrap; Spearman reranked within each draw',limited_clusters=g<10)
    if g<2:return result
    blocks=[np.flatnonzero(frame.acc.to_numpy()==protein) for protein in proteins]
    x=frame.depth.to_numpy();y=frame.agreement.to_numpy();rng=np.random.default_rng(seed)
    samples=[]
    for draw in rng.integers(0,g,size=(repeats,g)):
        ids=np.concatenate([blocks[j] for j in draw])
        # Duplicate assays from repeated selections are retained in the expanded draw.
        if len(np.unique(x[ids]))>1 and len(np.unique(y[ids]))>1:
            samples.append(float(spearmanr(x[ids],y[ids]).statistic))
    result['valid_bootstrap_draws']=len(samples)
    if len(samples)>=.95*repeats:
        result['low'],result['high']=map(float,np.quantile(samples,[.025,.975]))
    return result

assert accuracy.groupby('assay').acc.nunique().eq(1).all()
assert accuracy.groupby('acc').split.nunique().eq(1).all(), 'A protein cannot appear in both partitions'
depth_controls=[]
for label,subset in [('All',accuracy),('Excluding stability',accuracy[accuracy.selection!='Stability']),('Stability only',accuracy[accuracy.selection=='Stability']),('Discovery',accuracy[accuracy.split=='discovery']),('Confirmation',accuracy[accuracy.split=='confirmation'])]:
    depth_controls.append(dict(subset=label,**protein_bootstrap_spearman(subset)))
depth_controls=pd.DataFrame(depth_controls)
depth_controls.to_csv(OUT/'depth_controls.csv',index=False)
display(depth_controls)
print('No iid Spearman p-values are reported. These nominal intervals account for repeated assays within proteins, not exploratory multiplicity.')
fig,ax=plt.subplots(figsize=(7,4),constrained_layout=True)
for selection,group in accuracy.groupby('selection'):
    ax.scatter(np.log1p(group.depth),group.agreement,label=selection,alpha=.7,s=25)
ax.set(xlabel='log(1 + effective MSA sequences / alignment length)',ylabel='Within-assay |Spearman|',title='Whole-protein alignment depth')
ax.legend(frameon=False,fontsize=8)
show_figure(fig)
