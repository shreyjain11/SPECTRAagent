"""Apply the frozen STATE endpoint correction; no numerical analysis runs here."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
p=ROOT/'reproduction/inline/state/state-featured/test-03.ipynb'
b=json.loads(p.read_text())
def source(i):return ''.join(b['cells'][i]['source'])
def put(i,value):b['cells'][i]['source']=value.splitlines(keepends=True)
put(0,source(0).replace('lists of training genes','lists of reconstructed training-reference genes').replace('held-out cell types','the designated confirmation cell types'))
put(15,'''## 5. Curves and controls

Calculate per-level means from the individual condition rows. Higher overlap@N indicates better prediction. The plots keep each representation and discovery/confirmation subset separate. Standard-deviation columns describe spread between records, not uncertainty in a mean.

The annotated endpoint comparison preserves the row-weighted L2-minus-L1 difference. Its 95% percentile interval resamples canonical genes, retaining all of a sampled gene's rows across the two contexts and both levels together. There are 2,000 draws with seed 7. This accounts for recurring genes within each subset and representation; the interval is conditional on the observed contexts, annotations, reference construction and fixed cutpoints.

Only L1 and L2 are populated annotated levels. L0 means missing pathway annotation, not lower measured pathway similarity. The original all-group plot and descriptive `trends` tables are retained, but their L0-to-L2 comparisons and three-group counts are not the annotated endpoint result or evidence of a three-level similarity curve.
''')
old=source(16); start=old.index('def b_bootstrap_gap(');end=old.index('\ncurve=b_summarize_levels',start)
helper='''def b_bootstrap_gap(df: pd.DataFrame, level_col: str, metric: str,
                    low_levels: set[str], high_levels: set[str],
                    reps: int = 2000, seed: int = 7):
    """Row-weighted endpoint contrast; jointly resample complete canonical-gene blocks."""
    assert not (low_levels & high_levels), 'Endpoint levels must be disjoint'
    data = df[df[level_col].isin(low_levels | high_levels)].copy()
    data[metric] = pd.to_numeric(data[metric], errors='coerce')
    # This retains the original nonmissing-score population; infinity is an error.
    data = data.dropna(subset=[metric]).copy()
    assert np.isfinite(data[metric]).all(), 'Endpoint scores must be finite'
    assert data.gene_symbol_canonical.notna().all()
    assert data.gene_symbol_canonical.astype(str).str.len().gt(0).all()
    genes = np.array(sorted(data.gene_symbol_canonical.unique()))
    assert len(genes) >= 2, 'At least two independent gene clusters are needed'
    gene_index = pd.Index(genes).get_indexer(data.gene_symbol_canonical)
    score = data[metric].to_numpy(float)
    high = data[level_col].isin(high_levels).to_numpy()
    low = data[level_col].isin(low_levels).to_numpy()
    assert (low | high).all() and low.sum() >= 2 and high.sum() >= 2
    low_count = np.bincount(gene_index[low], minlength=len(genes))
    high_count = np.bincount(gene_index[high], minlength=len(genes))
    low_sum = np.bincount(gene_index[low], weights=score[low], minlength=len(genes))
    high_sum = np.bincount(gene_index[high], weights=score[high], minlength=len(genes))
    membership = pd.DataFrame({'gene_symbol_canonical': genes,
                               'low_n': low_count, 'high_n': high_count,
                               'low_score_sum': low_sum, 'high_score_sum': high_sum})
    context_counts = data.groupby('gene_symbol_canonical').context.nunique()
    membership['n_contexts'] = membership.gene_symbol_canonical.map(context_counts)
    rng = np.random.default_rng(seed)
    draws = []
    for draw in range(reps):
        # One multiplicity per gene, shared across every context and endpoint row.
        sampled = rng.choice(len(genes), size=len(genes), replace=True)
        multiplicity = np.bincount(sampled, minlength=len(genes))
        n_low = int(np.sum(multiplicity * low_count))
        n_high = int(np.sum(multiplicity * high_count))
        gap = (float(np.sum(multiplicity * high_sum) / n_high
                     - np.sum(multiplicity * low_sum) / n_low)
               if n_low and n_high else float('nan'))
        # Verify sufficient-statistic arithmetic against duplicated original rows.
        if draw < 5 and n_low and n_high:
            expanded = np.repeat(np.arange(len(data)), multiplicity[gene_index])
            expanded_gap = (score[expanded][high[expanded]].mean()
                            - score[expanded][low[expanded]].mean())
            assert np.isclose(gap, expanded_gap, atol=1e-12, rtol=1e-12)
        draws.append({'draw': draw, 'gap_high_minus_low': gap,
                      'low_rows': n_low, 'high_rows': n_high})
    draws = pd.DataFrame(draws)
    finite = draws.gap_high_minus_low[np.isfinite(draws.gap_high_minus_low)]
    assert len(finite) >= 2, 'Insufficient finite cluster draws for an interval'
    result = {'gap_high_minus_low': float(score[high].mean() - score[low].mean()),
              'ci_low': float(np.quantile(finite, 0.025)),
              'ci_high': float(np.quantile(finite, 0.975)),
              'low_n': int(low.sum()), 'high_n': int(high.sum()),
              'low_genes': int((low_count > 0).sum()),
              'high_genes': int((high_count > 0).sum()),
              'gene_clusters': int(len(genes)),
              'genes_in_both_levels': int(((low_count > 0) & (high_count > 0)).sum()),
              'genes_in_multiple_contexts': int((context_counts > 1).sum()),
              'bootstrap_draws': int(reps), 'finite_draws': int(len(finite)),
              'empty_endpoint_draws': int(((draws.low_rows == 0) | (draws.high_rows == 0)).sum()),
              'bootstrap_seed': int(seed), 'resampling_unit': 'canonical_gene'}
    return result, draws, membership
'''
put(16,old[:start]+helper+old[end:])
put(18,'''# Tied cutpoints leave two annotated levels; keep their original row-weighted contrast.
bootstrap_rows=[]
bootstrap_draw_tables=[]
bootstrap_membership_tables=[]
for (subset,representation),part in examples.groupby(['spectra_subset','representation']):
    populated=sorted(set(part[LEVEL].dropna())-{'L0_no_annotation'})
    assert len(populated)==2, 'This retained analysis has two populated annotated levels'
    contrast,draws,membership=b_bootstrap_gap(
        part,LEVEL,'overlap_at_N',{populated[0]},{populated[-1]},reps=2000,seed=7)
    contrast.update({'low_level':populated[0],'high_level':populated[-1],
                     'populated_annotated_levels':len(populated)})
    bootstrap_rows.append({'subset':subset,'representation':representation,**contrast})
    bootstrap_draw_tables.append(draws.assign(subset=subset,representation=representation))
    bootstrap_membership_tables.append(membership.assign(subset=subset,representation=representation))
bootstrap=pd.DataFrame(bootstrap_rows)
bootstrap_draws=pd.concat(bootstrap_draw_tables,ignore_index=True)
bootstrap_membership=pd.concat(bootstrap_membership_tables,ignore_index=True)
display(bootstrap)
bootstrap.to_csv(OUTPUTS/'bootstrap_contrasts.csv',index=False)
bootstrap_draws.to_csv(OUTPUTS/'bootstrap_draws.csv',index=False)
bootstrap_membership.to_csv(OUTPUTS/'bootstrap_gene_membership.csv',index=False)
''')
put(19,'''## 6. What the agent decided, and why

The conclusion below uses the annotated L2-minus-L1 overlap@N differences and their gene-cluster intervals, separately for HVG and SE in the designated Jurkat/RPE1 confirmation subset. It does not use the descriptive L0-to-L2 comparisons. Genes recurring across contexts or endpoints are resampled together.

This is a two-level association conditional on these contexts and the reconstructed training reference. Tied discovery cutpoints leave only L1 and L2 populated; L0 is missing annotation. The contrast does not establish a three-or-more-level degradation curve, a universal context-transfer relationship, causality, or completion of the full protocol. This computational correction uses the same released scores; it is not a new prospective confirmation experiment.
''')
put(20,'''confirmation=bootstrap[bootstrap['subset']=='confirmation_jurkat_rpe1'].copy()
assert set(confirmation.representation)=={'HVG','SE'} and len(confirmation)==2
assert (confirmation.populated_annotated_levels==2).all()
positive_in_both=(confirmation.gap_high_minus_low.gt(0) & confirmation.ci_low.gt(0)).all()
decision=(
    'Both representations show higher mean overlap@N in L2 than L1 within the pooled Jurkat/RPE1 rows; both gene-cluster 95% intervals are above zero.'
    if positive_in_both else
    'The annotated L2-minus-L1 difference is not consistently positive by both gene-cluster 95% intervals within the pooled Jurkat/RPE1 rows.')
print(decision)
display(confirmation[['subset','representation','low_level','high_level','gap_high_minus_low',
                      'ci_low','ci_high','low_n','high_n','gene_clusters','finite_draws']])
print('Two populated annotated levels; intervals are conditional on these contexts and fixed reference/cutpoints. This does not establish a three-level curve or full protocol completion.')
''')
put(21,source(21).replace("['per_condition_results.csv','curve.csv','trends.csv','curve.png']", "['per_condition_results.csv','curve.csv','trends.csv','context_trends.csv','curve.png',\n              'bootstrap_contrasts.csv','bootstrap_draws.csv','bootstrap_gene_membership.csv']"))
# Old outputs must not be mistaken for results of the corrected code before execution.
for c in b['cells']:
    if c['cell_type']=='code':
        c['execution_count']=None;c['outputs']=[];c['metadata'].pop('execution',None)
b['metadata'].pop('analysis_execution',None)
p.write_text(json.dumps(b,indent=1,ensure_ascii=False)+'\n')
print(p)
