# Protein-aware uncertainty for the existing assay-weighted estimands.
# Whole accession blocks are resampled; proteins are NOT collapsed to equally weighted means.
CLUSTER_BOOTSTRAP_DRAWS=10000
CLUSTER_SEED=20261116
SIGN_FLIP_DRAWS=50000

def protein_bootstrap_mean(values,proteins,repeats=CLUSTER_BOOTSTRAP_DRAWS,seed=CLUSTER_SEED):
    frame=pd.DataFrame({'value':np.asarray(values,dtype=float),'protein':np.asarray(proteins)})
    frame=frame[np.isfinite(frame.value)].copy()
    assert frame.protein.notna().all(), 'Every retained assay needs a protein accession'
    if frame.empty:return np.nan,np.nan,np.nan,0,0
    blocks=frame.groupby('protein',sort=True).value.agg(['sum','count'])
    g=len(blocks);point=float(frame.value.mean())
    if g<2:return point,np.nan,np.nan,len(frame),g
    rng=np.random.default_rng(seed)
    draws=rng.integers(0,g,size=(repeats,g))
    samples=blocks['sum'].to_numpy()[draws].sum(axis=1)/blocks['count'].to_numpy()[draws].sum(axis=1)
    low,high=np.quantile(samples,[.025,.975])
    return point,float(low),float(high),len(frame),g

def protein_sign_flip(values,proteins,draws=SIGN_FLIP_DRAWS,seed=CLUSTER_SEED):
    # The null requires joint sign symmetry of each protein's assay-contrast vector.
    # This is not an independent-assay Wilcoxon test or a distribution-free test of zero mean.
    frame=pd.DataFrame({'value':np.asarray(values,dtype=float),'protein':np.asarray(proteins)})
    frame=frame[np.isfinite(frame.value)].copy()
    assert frame.protein.notna().all()
    sums=frame.groupby('protein',sort=True).value.sum().to_numpy();g=len(sums)
    if g<2:return np.nan,'unavailable: fewer than two proteins'
    observed=abs(float(sums.sum()))
    tolerance=32*np.finfo(float).eps*max(1.0,float(np.abs(sums).sum()))
    if g<=16:
        patterns=np.arange(1<<g,dtype=np.uint64)[:,None]
        signs=2*((patterns>>np.arange(g,dtype=np.uint64))&1).astype(float)-1
        null=np.abs(signs@sums)
        return float(np.mean(null>=observed-tolerance)),'exact protein-block sign flip'
    rng=np.random.default_rng(seed)
    signs=2*rng.integers(0,2,size=(draws,g),dtype=np.int8)-1
    null=np.abs(signs@sums)
    return float((np.count_nonzero(null>=observed-tolerance)+1)/(draws+1)),'Monte Carlo protein-block sign flip'

assert scores.groupby('assay').acc.nunique().eq(1).all()
assert scores.groupby('acc').split.nunique().eq(1).all(), 'A protein cannot appear in both partitions'
curve_rows=[]
fig,axes=plt.subplots(1,scores.scheme.nunique(),figsize=(6*scores.scheme.nunique(),4),squeeze=False,constrained_layout=True)
for ax,(scheme,group) in zip(axes.ravel(),scores.groupby('scheme',sort=True)):
    for method in ['AM','BLOSUM','PSSM']:
        points=[]
        for level,cell in group.groupby('level'):
            mean,low,high,count,g=protein_bootstrap_mean(cell[method],cell.acc)
            record=dict(scheme=scheme,method=method,level=level,mean=mean,low=low,high=high,n_assays=count,n_proteins=g,
                        interval_method='protein-block percentile bootstrap; assay-weighted mean',limited_clusters=g<10)
            points.append(record);curve_rows.append(record)
        points=pd.DataFrame(points)
        ax.errorbar(points.level,points['mean'],yerr=[points['mean']-points.low,points.high-points['mean']],marker='o',capsize=3,label=method)
    levels=sorted(group.level.unique())
    ax.set(xticks=levels,xticklabels=LEVEL_LABELS[scheme],xlabel=AXIS_LABEL,ylabel='Mean within-assay |Spearman|',title=scheme)
    ax.legend(frameon=False)
show_figure(fig)
curves=pd.DataFrame(curve_rows);curves.to_csv(OUT/'curves.csv',index=False)
display(curves)

def paired_effects(table,label):
    result=[]
    for scheme,group in table.groupby('scheme'):
        pivots={method:group.pivot(index='assay',columns='level',values=method) for method in ['AM','BLOSUM','PSSM']}
        low=min(scores.loc[scores.scheme==scheme,'level']);high=max(scores.loc[scores.scheme==scheme,'level'])
        common=None
        for pivot in pivots.values():
            eligible=set(pivot.reindex(columns=[low,high]).dropna().index)
            common=eligible if common is None else common & eligible
        ids=sorted(common or [])
        mapping=group[['assay','acc']].drop_duplicates().set_index('assay').acc
        proteins=mapping.reindex(ids).to_numpy()
        delta={method:(pivot.reindex(index=ids,columns=[low,high])[high]-pivot.reindex(index=ids,columns=[low,high])[low]).to_numpy() for method,pivot in pivots.items()}
        comparisons={**delta,'AM minus BLOSUM':delta['AM']-delta['BLOSUM'],'AM minus PSSM':delta['AM']-delta['PSSM']}
        for comparison,values in comparisons.items():
            mean,lo,hi,count,g=protein_bootstrap_mean(values,proteins)
            p,test=protein_sign_flip(values,proteins)
            result.append(dict(subset=label,scheme=scheme,comparison=comparison,mean=mean,low=lo,high=hi,
                               n_assays=count,n_proteins=g,limited_clusters=g<10,
                               interval_method='protein-block percentile bootstrap; assay-weighted mean',
                               sign_flip_p=p,sign_flip_method=test))
    return result

effects=[]
for label,table in [('All',scores),('Discovery',scores[scores.split=='discovery']),('Confirmation',scores[scores.split=='confirmation']),('Excluding stability',scores[scores.selection!='Stability'])]:
    effects.extend(paired_effects(table,label))
if RUN==1:effects.extend(paired_effects(scores[scores.total_hits>=30],'At least 30 homologs'))
effects=pd.DataFrame(effects);effects.to_csv(OUT/'paired_effects.csv',index=False)
display(effects)
print('Intervals resample entire proteins and retain the assay-weighted mean. Tests assume joint sign symmetry within protein blocks.')
print('Intervals and tests are nominal, not corrected for the multiple exploratory comparisons; fewer than ten proteins is marked limited_clusters.')
display(scores.groupby(['scheme','level']).dms_std.mean().rename('DMS dynamic range'))
