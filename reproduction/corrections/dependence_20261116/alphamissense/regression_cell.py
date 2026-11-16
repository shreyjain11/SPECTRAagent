from scipy.stats import t as student_t

def adjusted_control(binby):
    rows=[]
    for assay,group in variants.dropna(subset=['coverage','plddt']).groupby('assay'):
        group=group.copy()
        group['cell']=pd.qcut(group[binby],6,labels=False,duplicates='drop')
        assert group.acc.nunique()==1
        for cell,subset in group.groupby('cell'):
            rows.append(dict(assay=assay,acc=subset.acc.iloc[0],am=agreement(subset,'am_pathogenicity'),coverage=subset.coverage.mean(),plddt=subset.plddt.mean(),log_dms_sd=np.log(subset.DMS_score.std()+1e-9)))
    cells=pd.DataFrame(rows).replace([np.inf,-np.inf],np.nan).dropna()
    columns=['coverage','plddt','log_dms_sd']
    for column in ['am']+columns:cells[column+'_centered']=cells[column]-cells.groupby('assay')[column].transform('mean')
    x=np.column_stack([np.ones(len(cells))]+[cells[column+'_centered'] for column in columns]);y=cells.am_centered.to_numpy()
    beta=np.linalg.lstsq(x,y,rcond=None)[0];residual=y-x@beta
    rank=np.linalg.matrix_rank(x);n=len(cells);a=cells.assay.nunique()
    # Absorbed assay intercepts consume degrees of freedom even after within-assay centering.
    full_design=np.column_stack([pd.get_dummies(cells.assay,dtype=float).to_numpy(),x[:,1:]])
    effective_rank=int(np.linalg.matrix_rank(full_design))
    assert rank==len(columns)+1 and effective_rank==a+len(columns), 'Nonidentifiable adjusted coefficients: full-rank fixed-effect design required'
    cluster_codes,protein_names=pd.factorize(cells.acc,sort=True);g=len(protein_names)
    score_sums=np.zeros((g,x.shape[1]))
    np.add.at(score_sums,cluster_codes,x*residual[:,None])
    bread=np.linalg.pinv(x.T@x)
    if g>=2 and n>effective_rank:
        cr1=g/(g-1)*(n-1)/(n-effective_rank)
        covariance=cr1*bread@(score_sums.T@score_sums)@bread
        se=np.sqrt(np.maximum(np.diag(covariance),0))
        critical=float(student_t.ppf(.975,g-1))
    else:
        cr1=np.nan;se=np.full(x.shape[1],np.nan);critical=np.nan
    cells.to_csv(OUT/f'control_cells_{binby}.csv',index=False)
    result=[]
    for i,column in enumerate(columns):
        estimate=float(beta[i+1]);error=float(se[i+1]);statistic=estimate/error if error>0 else np.nan
        result.append(dict(binning=binby,covariate=column,beta=estimate,standard_error=error,
                           ci_low=estimate-critical*error,ci_high=estimate+critical*error,t=statistic,
                           p_two_sided=float(2*student_t.sf(abs(statistic),g-1)) if np.isfinite(statistic) else np.nan,
                           cells=n,n_assays=a,n_proteins=g,rank=int(rank),effective_parameter_rank=effective_rank,
                           residual_df=n-effective_rank,cluster_df=g-1,cr1_factor=cr1,
                           covariance='CR1 protein clusters; absorbed assay fixed effects; t(G-1)',limited_clusters=g<10))
    return result
adjusted=pd.DataFrame(adjusted_control('coverage')+adjusted_control('plddt'))
adjusted.to_csv(OUT/'adjusted_controls.csv',index=False);display(adjusted)
print('Point estimates retain within-assay OLS centering. Uncertainty clusters all bins and assays of a protein, with full assay fixed-effect degrees of freedom.')
