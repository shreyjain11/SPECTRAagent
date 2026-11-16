"""Independent checks of the endpoint correction against exact retained condition rows."""
from pathlib import Path
from datetime import datetime, timezone
import gzip, hashlib, json, re, shutil, sys
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
WORK=Path('/private/tmp/state-test03-dependence-20261116')
BEFORE=WORK/'before/state_primary_outputs/test-03'
AFTER=WORK/'after/state_primary_outputs/test-03'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

# The original plan is immutable and precedes both numerical executions.
assert sha(HERE/'PLAN.json')==(HERE/'PLAN.sha256').read_text().split()[0]
plan=json.loads((HERE/'PLAN.json').read_text())
pre_execution=json.loads((HERE/'before-execution.json').read_text())
post_execution=json.loads((HERE/'after-execution.json').read_text())
assert plan['frozen_at_utc']<pre_execution['started_at']<pre_execution['finished_at']<post_execution['started_at']
assert pre_execution['completed'] and post_execution['completed']
original=json.loads(gzip.decompress((HERE/'original.ipynb.gz').read_bytes()))
book=json.loads((ROOT/'reproduction/inline/state/state-featured/test-03.ipynb').read_text())
changed_sources=[i for i,(a,b) in enumerate(zip(original['cells'],book['cells'])) if a['source']!=b['source']]
assert set(changed_sources)=={0,15,16,18,19,20,21},changed_sources
indices=[i for i,c in enumerate(book['cells']) if c['cell_type']=='code']
assert len(indices)==13 and indices==post_execution['executed_notebook_cells']
assert [book['cells'][i]['execution_count'] for i in indices]==list(range(1,14))
assert not [o for i in indices for o in book['cells'][i]['outputs'] if o['output_type']=='error']
sections=[]
for i,c in enumerate(book['cells']):
 if c['cell_type']=='markdown':
  for m in re.finditer(r'^## ([1-6])\. ',''.join(c['source']),re.M):sections.append((int(m[1]),i))
assert [x[0] for x in sections]==list(range(1,7))
assert all(any(start<i<end for i in indices) for (_,start),(_,end) in zip(sections,sections[1:]+[(7,len(book['cells']))]))

# Identical bytes establish unchanged records, canonicalization, contexts, scores,
# features, cutpoints/level assignment and descriptive curve calculations.
unchanged={}
for name in ['per_condition_results.csv','curve.csv','trends.csv','context_trends.csv','curve.png']:
 same=sha(BEFORE/name)==sha(AFTER/name)
 assert same,(name,'changed outside endpoint uncertainty')
 unchanged[name]={'sha256':sha(AFTER/name),'bytes':(AFTER/name).stat().st_size,'before_equals_after':same}
assert original['cells'][3]['source']==book['cells'][3]['source']
assert original['cells'][10]['source']==book['cells'][10]['source']
assert original['cells'][12]['source']==book['cells'][12]['source']

# Independently verify every consumed public input from the executed receipt.
input_receipt=json.loads((AFTER/'execution_record.json').read_text())
cache=Path('/private/tmp/state-primary-correction-inputs')
for entry in input_receipt['source_files']:
 path=cache/entry['path']
 assert path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256'],entry['path']
(HERE/'input-manifest.json').write_text(json.dumps({'analysis_id':plan['analysis_id'],'cache_location_at_execution':str(cache),'files':input_receipt['source_files'],'all_actual_cached_bytes_verified':True},indent=2)+'\n')

rows=pd.read_csv(AFTER/'per_condition_results.csv')
summary=pd.read_csv(AFTER/'bootstrap_contrasts.csv')
old=pd.read_csv(BEFORE/'bootstrap_contrasts.csv')
saved_draws=pd.read_csv(AFTER/'bootstrap_draws.csv')
saved_membership=pd.read_csv(AFTER/'bootstrap_gene_membership.csv')
checks=[]
for _,result in summary.iterrows():
 part=rows[(rows.spectra_subset==result['subset']) & (rows.representation==result['representation'])]
 level='reactome_support_level'; metric='overlap_at_N'
 assert sorted(set(part[level]) - {'L0_no_annotation'})==['L1_low','L2_mid']
 eligible=part[part[level].isin(['L1_low','L2_mid']) & part[metric].notna()].copy()
 assert np.isfinite(eligible[metric]).all()
 genes=sorted(eligible.gene_symbol_canonical.unique())
 # Independent implementation expands actual full gene blocks. It does not use
 # the notebook helper or saved sufficient statistics to calculate any draw.
 groups={gene:eligible[eligible.gene_symbol_canonical==gene][[level,metric]].to_numpy() for gene in genes}
 rng=np.random.default_rng(7); differences=[]; low_sizes=[];high_sizes=[]
 for draw in range(2000):
  picks=rng.choice(len(genes),size=len(genes),replace=True)
  expanded=np.concatenate([groups[genes[i]] for i in picks])
  low=expanded[expanded[:,0]=='L1_low',1].astype(float)
  high=expanded[expanded[:,0]=='L2_mid',1].astype(float)
  differences.append(high.mean()-low.mean() if len(high) and len(low) else np.nan)
  low_sizes.append(len(low));high_sizes.append(len(high))
 expected=saved_draws[(saved_draws['subset']==result['subset']) & (saved_draws.representation==result['representation'])].sort_values('draw')
 np.testing.assert_allclose(differences,expected.gap_high_minus_low,atol=1e-12,rtol=1e-12)
 np.testing.assert_array_equal(low_sizes,expected.low_rows)
 np.testing.assert_array_equal(high_sizes,expected.high_rows)
 finite=np.asarray(differences)[np.isfinite(differences)]
 ci=np.quantile(finite,[.025,.975])
 np.testing.assert_allclose(ci,[result.ci_low,result.ci_high],atol=1e-12,rtol=1e-12)
 point=eligible[eligible[level]=='L2_mid'][metric].mean()-eligible[eligible[level]=='L1_low'][metric].mean()
 previous=old[(old['subset']==result['subset']) & (old.representation==result['representation'])].iloc[0]
 np.testing.assert_allclose([point,previous.gap_high_minus_low],[result.gap_high_minus_low]*2,atol=1e-14,rtol=1e-14)
 member=saved_membership[(saved_membership['subset']==result['subset']) & (saved_membership.representation==result['representation'])].set_index('gene_symbol_canonical')
 actual=eligible.groupby(['gene_symbol_canonical',level])[metric].agg(['size','sum']).unstack(level).fillna(0).reindex(genes)
 np.testing.assert_array_equal(actual['size']['L1_low'],member.loc[genes,'low_n'])
 np.testing.assert_array_equal(actual['size']['L2_mid'],member.loc[genes,'high_n'])
 np.testing.assert_allclose(actual['sum']['L1_low'],member.loc[genes,'low_score_sum'],atol=1e-12,rtol=1e-12)
 np.testing.assert_allclose(actual['sum']['L2_mid'],member.loc[genes,'high_score_sum'],atol=1e-12,rtol=1e-12)
 checks.append({'subset':result['subset'],'representation':result['representation'],'point_estimate_unchanged':True,'all_2000_draws_match_independent_expanded_blocks':True,'rows':len(eligible),'gene_clusters':len(genes),'genes_in_both_levels':int(eligible.groupby('gene_symbol_canonical')[level].nunique().gt(1).sum()),'genes_in_multiple_contexts':int(eligible.groupby('gene_symbol_canonical').context.nunique().gt(1).sum()),'finite_draws':int(len(finite)),'ci_low':float(ci[0]),'ci_high':float(ci[1]),'point':float(point)})

comparison=old.merge(summary,on=['subset','representation'],suffixes=('_row_bootstrap','_gene_bootstrap'),validate='one_to_one')
comparison.to_csv(HERE/'before-after-contrasts.csv',index=False)
confirmation=summary[summary['subset']=='confirmation_jurkat_rpe1']
assert len(confirmation)==2 and (confirmation.ci_low>0).all()
text=''.join(o.get('text','') if isinstance(o.get('text',''),str) else ''.join(o['text']) for o in book['cells'][20]['outputs'] if o['output_type']=='stream')
assert 'Both representations show higher mean overlap@N in L2 than L1' in text
assert 'does not establish a three-level curve or full protocol completion' in text
assert 'Accept support-related' not in text

(HERE/'after').mkdir(exist_ok=True)
for name in ['bootstrap_contrasts.csv','bootstrap_draws.csv','bootstrap_gene_membership.csv','curve.csv','trends.csv','context_trends.csv','execution_record.json']:
 shutil.copy2(AFTER/name,HERE/'after'/name)
# The exact individual records are compacted losslessly for independent replay.
(HERE/'per-condition-results.csv.gz').write_bytes(gzip.compress((AFTER/'per_condition_results.csv').read_bytes(),mtime=0))
report={'verified_at_utc':datetime.now(timezone.utc).isoformat(),'analysis_id':plan['analysis_id'],'verification_python':sys.version,'verification_driver_sha256':sha(__file__),'plan_sha256':sha(HERE/'PLAN.json'),'original_notebook_sha256':plan['original_notebook_sha256'],'corrected_executed_notebook_sha256':sha(ROOT/'reproduction/inline/state/state-featured/test-03.ipynb'),'all_13_code_cells_executed_in_fresh_kernel':True,'six_sections_have_executed_code':True,'no_error_outputs':True,'changed_source_cells':changed_sources,'unchanged_outputs':unchanged,'verified_public_input_files':len(input_receipt['source_files']),'bootstrap_checks':checks,'interpretation_uses_annotated_gene_intervals':True,'limits':['Two populated annotated levels, not three or more informative similarity levels','Intervals conditional on fixed contexts, reference and annotations','Reconstructed training reference; not recovered original training manifest','Computational correction of released scores, not new inference or new prospective confirmation','Separate representation-specific intervals; no combined or simultaneous inference across representations']}
(HERE/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
