import collections,datetime,hashlib,json,pathlib
import numpy as np
import pandas as pd
BASE=pathlib.Path('/private/tmp/state-test03-dependence-20261116')
REPO=pathlib.Path(__file__).resolve().parents[4]
OUT=pathlib.Path(__file__).parent
paths={stage:BASE/stage/'state_primary_outputs/test-03' for stage in ['before','after']}
old=pd.read_csv(paths['before']/'per_condition_results.csv');new=pd.read_csv(paths['after']/'per_condition_results.csv')
pd.testing.assert_frame_equal(old,new,check_exact=True)
for name in ['curve.csv','trends.csv','context_trends.csv']:
 pd.testing.assert_frame_equal(pd.read_csv(paths['before']/name),pd.read_csv(paths['after']/name),check_exact=True)
summary=pd.read_csv(paths['after']/'bootstrap_contrasts.csv');draws=pd.read_csv(paths['after']/'bootstrap_draws.csv');membership=pd.read_csv(paths['after']/'bootstrap_gene_membership.csv')
records=[]
for _,s in summary.iterrows():
 frame=new[(new.spectra_subset==s['subset'])&(new.representation==s.representation)&new.reactome_support_level.isin([s.low_level,s.high_level])].dropna(subset=['overlap_at_N']).reset_index(drop=True)
 keys=sorted(frame.gene_symbol_canonical.unique());indices={key:np.flatnonzero(frame.gene_symbol_canonical.to_numpy()==key) for key in keys}
 scores=frame.overlap_at_N.to_numpy();high=frame.reactome_support_level.eq(s.high_level).to_numpy()
 rng=np.random.default_rng(int(s.bootstrap_seed));expected=[];counts=[]
 # Expand actual original rows for every draw, independently of the saved sufficient-statistic method.
 for iteration in range(int(s.bootstrap_draws)):
  selected=rng.choice(len(keys),size=len(keys),replace=True)
  expanded=np.concatenate([indices[keys[i]] for i in selected])
  hi=high[expanded];yy=scores[expanded]
  expected.append(yy[hi].mean()-yy[~hi].mean())
  counts.append((int((~hi).sum()),int(hi.sum())))
 expected=np.asarray(expected);saved=draws[(draws['subset']==s['subset'])&(draws.representation==s.representation)].sort_values('draw')
 assert len(saved)==len(expected)
 maximum=float(np.max(np.abs(saved.gap_high_minus_low.to_numpy()-expected)));assert maximum<1e-12
 assert np.array_equal(saved[['low_rows','high_rows']].to_numpy(),counts)
 ci=np.quantile(expected,[.025,.975]);point=float(scores[high].mean()-scores[~high].mean())
 assert np.allclose(ci,[s.ci_low,s.ci_high],atol=1e-12,rtol=0)
 assert abs(point-s.gap_high_minus_low)<1e-12
 assert len(keys)==s.gene_clusters
 m=membership[(membership['subset']==s['subset'])&(membership.representation==s.representation)]
 assert set(m.gene_symbol_canonical)==set(keys)
 for _,row in m.iterrows():
  g=frame[frame.gene_symbol_canonical==row.gene_symbol_canonical];lo=g[g.reactome_support_level==s.low_level];hi=g[g.reactome_support_level==s.high_level]
  assert len(lo)==row.low_n and len(hi)==row.high_n
  assert np.isclose(lo.overlap_at_N.sum(),row.low_score_sum,atol=1e-12,rtol=0)
  assert np.isclose(hi.overlap_at_N.sum(),row.high_score_sum,atol=1e-12,rtol=0)
  assert g.context.nunique()==row.n_contexts
 records.append({'subset':s['subset'],'representation':s.representation,'endpoint_levels':[s.low_level,s.high_level],'row_count':len(frame),'canonical_genes':len(keys),'genes_crossing_endpoints':int(s.genes_in_both_levels),'point':point,'ci95':ci.tolist(),'expanded_row_draws_checked':len(expected),'maximum_absolute_draw_difference':maximum,'all_draw_endpoint_counts_match':True,'all_gene_membership_sufficient_statistics_match':True})
book=json.loads((REPO/'reproduction/inline/state/state-featured/test-03.ipynb').read_text())
outputs='\n'.join(''.join(o.get('text',[])) for o in book['cells'][20]['outputs'])
assert 'L2 than L1' in outputs and 'does not establish a three-level curve or full protocol completion' in outputs
assert all(c['execution_count'] is not None for c in book['cells'] if c['cell_type']=='code')
result={'checked_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'analysis':'state-featured/test-03','method':'Independently reconstruct every bootstrap draw by physically concatenating all original rows for each sampled gene; recompute endpoint means without using notebook helpers or saved cluster sums.','all_individual_rows_and_curves_unchanged':True,'source_files':{str(paths['after']/x):hashlib.sha256((paths['after']/x).read_bytes()).hexdigest() for x in ['per_condition_results.csv','bootstrap_contrasts.csv','bootstrap_draws.csv','bootstrap_gene_membership.csv']},'strata':records,'scoped_interpretation_matches_corrected_annotated_contrasts':True,'limitations':['Conditional on retained contexts, gene-reference reconstruction, annotation snapshots and frozen cutpoints.','Only two annotated levels: no three-level curve or full-protocol-completion conclusion.','This review verifies the dependency correction and unchanged saved-score analysis, not fresh model inference.'],'issues':[]}
(OUT/'state-numerical-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'strata':len(records),'draws':sum(r['expanded_row_draws_checked'] for r in records),'max_error':max(r['maximum_absolute_draw_difference'] for r in records),'issues':[]},indent=2))
