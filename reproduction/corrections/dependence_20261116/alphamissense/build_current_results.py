"""Bind current summary metadata to tables exported by the six full executions."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent;R=HERE.parents[2]
records={}
for p in sorted((HERE/'outputs').glob('am-opus-r*-test-*/CURRENT_RESULTS.json')):
 result=json.loads(p.read_text())
 result['interpretation']=result['decision']+'. '+result['scope']
 if result['analysis_id'].endswith('/test-02'):
  result['aggregation_and_uncertainty']='Spearman correlation across the original assay rows. Percentile 95% intervals use 10,000 whole-protein bootstrap draws, retaining all assays of each selected protein and reranking each expanded draw. No iid analytic p-values or bootstrap-tail p-values. Assay and protein counts are reported; intervals are nominal and are not adjusted for the exploratory comparisons.'
 else:
  result['aggregation_and_uncertainty']='Arithmetic means of eligible assay-level absolute Spearman correlations and matched assay-level endpoint contrasts, preserving assay weighting. Percentile 95% intervals use 10,000 whole-protein bootstrap draws. Two-sided protein-block sign-flip tests use exact enumeration for at most 16 proteins or 50,000 Monte Carlo draws otherwise and assume joint sign symmetry within each protein. All assays of one protein move together; assay/protein counts and limited-cluster flags are reported. Intervals/tests are nominal and are not multiplicity-adjusted.'
  if 'adjusted_controls' in result:
   result['aggregation_and_uncertainty']+=' Adjusted controls retain within-assay OLS coefficients and use CR1 protein-cluster covariance with full absorbed assay-fixed-effect rank and t(G−1) intervals/tests.'
 records[result['analysis_id']]=result
assert len(records)==6
(HERE/'current_results.json').write_text(json.dumps(records,indent=2)+'\n')
registration=json.loads((HERE/'registration.json').read_text())
for item in registration:
 item['output_artifacts']=sorted(set(item['output_artifacts']+[str((HERE/'current_results.json').relative_to(R))]))
 # Include the summary construction script separately; the notebook exports the numerical inputs verbatim.
 item['summary']='Reexecuted all code cells with protein-aware uncertainty and the corrected 273,135-variant score join; original assay weighting and axis definitions are retained. Historical-to-current numerical replay differences are reported separately.'
 item['dependency_scope']=item['dependency_scope'].split(' The combined current_results.json')[0]
 item['dependency_scope']+=' The combined current_results.json is assembled directly from each notebook\'s exported CURRENT_RESULTS.json by corrections/dependence_20261116/alphamissense/build_current_results.py. This full raw reconstruction is not claimed to reproduce historical floating-point values byte for byte.'
(HERE/'registration.json').write_text(json.dumps(registration,indent=2)+'\n')
print('Bound exact current numerical results for',len(records),'analyses')
