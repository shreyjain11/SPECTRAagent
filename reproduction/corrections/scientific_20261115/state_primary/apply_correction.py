"""Apply the declared regression correction to the three shared notebooks."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
FUNCTION='''def c_standardized_ols(df: pd.DataFrame, y_col: str, include_de_count: bool) -> dict[str, object]:
    from scipy.stats import t as student_t
    required = [y_col, c_SUPPORT_COL, 'reactome_pathway_count', 'gene_symbol_canonical', 'context', 'representation']
    if include_de_count:
        required.append('de_nsig_counts_real')
    eligible = df[pd.to_numeric(df['reactome_pathway_count'], errors='coerce') > 0].copy()
    work = eligible.dropna(subset=required).copy()
    numeric = [y_col, c_SUPPORT_COL, 'reactome_pathway_count']
    if include_de_count:
        numeric.append('de_nsig_counts_real')
    work[numeric] = work[numeric].apply(pd.to_numeric, errors='coerce')
    work = work[np.isfinite(work[numeric]).all(axis=1)].copy()
    if include_de_count and (work['de_nsig_counts_real'] < 0).any():
        raise ValueError('DE counts cannot be negative')
    y = work[y_col].to_numpy(float)
    columns, names = [], []
    def add_standardized(name, values):
        values = np.asarray(values, dtype=float)
        sd = values.std(ddof=0)
        if not np.isfinite(sd) or sd <= 0:
            raise ValueError('Constant or invalid covariate: ' + name)
        columns.append((values - values.mean()) / sd)
        names.append(name)
    add_standardized('support_log_mean_z', work[c_SUPPORT_COL])
    add_standardized('reactome_pathway_count_z', work['reactome_pathway_count'])
    if include_de_count:
        add_standardized('log1p_de_nsig_counts_real_z', np.log1p(work['de_nsig_counts_real']))
    reference_categories = {}
    for col in ['context', 'representation']:
        categories = sorted(work[col].astype(str).unique())
        reference_categories[col] = categories[0]
        for value in categories[1:]:
            columns.append(work[col].astype(str).eq(value).to_numpy(float))
            names.append(col + '_' + value)
    x = np.column_stack([np.ones(len(work)), *columns])
    n, p = x.shape
    rank = int(np.linalg.matrix_rank(x))
    if rank != p or n <= p:
        raise ValueError('Regression design must have full column rank and residual degrees of freedom')
    groups, genes = pd.factorize(work['gene_symbol_canonical'].astype(str), sort=True)
    g = len(genes)
    if g < 2:
        raise ValueError('Gene-clustered inference requires at least two genes')
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    residual = y - np.einsum('ij,j->i', x, beta, optimize=False)
    # All observations of a canonical gene contribute to one cluster score.
    cluster_scores = np.zeros((g, p))
    np.add.at(cluster_scores, groups, x * residual[:, None])
    bread = np.linalg.inv(np.einsum('ij,ik->jk', x, x, optimize=False))
    correction = (g / (g - 1)) * ((n - 1) / (n - p))
    covariance = correction * np.einsum('ij,jk,kl->il', bread, np.einsum('ij,ik->jk', cluster_scores, cluster_scores, optimize=False), bread, optimize=False)
    se = np.sqrt(np.maximum(np.diag(covariance), 0))
    critical = float(student_t.ppf(.975, g - 1))
    ss_total = float(np.sum((y - y.mean()) ** 2))
    coefs = []
    for name, estimate, error in zip(['intercept', *names], beta, se):
        statistic = float(estimate / error) if error > 0 else np.nan
        coefs.append({'term': name, 'coef': float(estimate), 'se': float(error),
                      'ci_low': float(estimate - critical * error), 'ci_high': float(estimate + critical * error),
                      't': statistic, 'p_two_sided': float(2 * student_t.sf(abs(statistic), g - 1)),
                      'n_gene_clusters': g, 'cluster_df': g - 1, 'design_rank': rank,
                      'n_design_columns': p, 'n_excluded_missing': int(len(eligible) - n),
                      'covariance': 'CR1 canonical-gene clusters; t(G-1)',
                      'reference_categories': json.dumps(reference_categories, sort_keys=True)})
    return {'n_rows': n, 'n_gene_clusters': g, 'design_rank': rank,
            'r2': 1 - float(np.sum(residual ** 2)) / ss_total if ss_total else np.nan,
            'include_de_count': include_de_count, 'coefficients': coefs}

'''
for test in ['05','09','10']:
    path=ROOT/'inline/state/state-featured'/f'test-{test}.ipynb'
    book=json.loads(path.read_text())
    cell=book['cells'][19]
    source=''.join(cell['source'])
    begin=source.index('def c_standardized_ols(');end=source.index('def c_matched_pathway_count_gaps',begin)
    source=source[:begin]+FUNCTION+source[end:]
    cell['source']=source.splitlines(keepends=True)
    book['cells'][18]['source']=('Exclude the unannotated level, compare support extremes within each context, and stratify the extreme groups into pathway-count quartiles. These are within-benchmark controls, not independent replication.\n\n'
        'The two regression specifications retain the same continuous covariates, context indicators and representation indicator. Subset indicators are omitted because subset is determined by context. Canonical genes define the uncertainty clusters across repeated contexts and representations. The reported 95% intervals use finite-sample-corrected cluster covariance and t quantiles with one fewer degree of freedom than the number of genes. Missing required covariates are excluded and counted; missing DE counts are not set to zero.\n').splitlines(keepends=True)
    if test=='10':
        book['cells'][21]['source']="""support_coefficients=regressions[regressions.term=='support_log_mean_z']
positive_intervals=support_coefficients.ci_low.gt(0).all()
decision=('The support coefficient is positive with a gene-clustered 95% interval above zero in both specified adjustments.' if positive_intervals else 'At least one specified adjustment has a gene-clustered interval that includes zero or is negative; a consistent adjusted association is not established.')
print(decision)
display(support_coefficients)
print('Inference is conditional on the observed cell contexts and the specified model; it does not establish a causal effect or transfer to new contexts.')
""".splitlines(keepends=True)
        book['cells'][20]['source']=('## 6. What the agent decided, and why\n\nThe decision below uses the canonical-gene-clustered intervals for both specified models. Adjustment for observed response strength is a sensitivity analysis; it does not identify a causal support effect. The contexts are fixed, observed benchmark contexts.\n').splitlines(keepends=True)
    else:
        s=''.join(book['cells'][21]['source']).replace("decision='Accept support-related degradation on the tested confirmation contexts' if supported else 'Reject consistent support-related degradation on the tested confirmation contexts'", "decision='Higher support has greater mean overlap in each displayed confirmation contrast.' if supported else 'The displayed confirmation contrasts do not all favor higher support.'")
        s+="\nprint('The endpoint direction is descriptive; the adjusted association and its gene-clustered uncertainty are reported separately above.')\n"
        book['cells'][21]['source']=s.splitlines(keepends=True)
        book['cells'][20]['source']=('## 6. What the agent decided, and why\n\nThe displayed endpoint contrasts summarize the measured support association. The separate regression table reports canonical-gene-clustered uncertainty for repeated genes. Neither endpoint signs nor adjusted coefficients establish a full protocol result or independent external confirmation.\n').splitlines(keepends=True)
    path.write_text(json.dumps(book,indent=1,ensure_ascii=False)+'\n')
print('Updated shared regression in tests 05, 09 and 10')
