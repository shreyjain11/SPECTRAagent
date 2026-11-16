"""Apply the frozen dependence repair; all scientific helpers are copied inline."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent
R=HERE.parents[2]
for p in sorted((R/'inline/alphamissense').glob('am-opus-r*/test-*.ipynb')):
 n=json.loads(p.read_text());run=int(p.parent.name[-1]);test=int(p.stem[-2:])
 def setcell(i,s):n['cells'][i]['source']=s.splitlines(keepends=True)
 if test==2:
  setcell(14,(HERE/'depth_cell.py').read_text())
  setcell(13,'Plot the existing assay-level measurements and assess the depth–performance association across all assays, after removing stability assays, within stability assays, and in the protein-separated discovery and confirmation groups.\n\nThe point estimate remains Spearman correlation across assay rows. Each 95% interval resamples entire proteins and reranks the expanded assay rows, retaining repeated assays of a protein together. Both assay and protein counts are shown.\n')
  setcell(15,'## 6. Decision and reason\n\nThis is a continuous screen of 73 assays from 64 proteins. The reported intervals account for repeated assays within proteins and are nominal, without adjustment for the multiple exploratory checks. No iid analytic Spearman p-values are used. An interval including zero does not establish absence of an effect. These reconstructed partitions do not establish independence from historical axis selection.\n')
  setcell(16,"""pooled=depth_controls.loc[depth_controls.subset=='All'].iloc[0]
controlled=depth_controls.loc[depth_controls.subset=='Excluding stability'].iloc[0]
consistent=pooled.low>0 and controlled.low>0 and min(pooled.n_proteins,controlled.n_proteins)>=10
decision='Both declared protein-cluster intervals support a positive depth association within this panel' if consistent else 'The declared protein-cluster intervals do not establish a consistently positive depth association'
display(Markdown(f'**{decision}.** Pooled Spearman: {pooled.rho:.3f} (95% interval {pooled.low:.3f} to {pooled.high:.3f}; {int(pooled.n_assays)} assays, {int(pooled.n_proteins)} proteins). Excluding stability: {controlled.rho:.3f} (95% interval {controlled.low:.3f} to {controlled.high:.3f}; {int(controlled.n_assays)} assays, {int(controlled.n_proteins)} proteins).'))
""")
 else:
  index=18 if run==1 else 19
  setcell(index,(HERE/'cluster_mean_cell.py').read_text())
  setcell(index-1,'Curves retain the mean of eligible within-assay correlations. Their 95% intervals resample whole proteins, carrying all eligible assays of each selected protein into the draw. Paired highest-minus-lowest effects retain the same common assays for all three predictors and the same assay-weighted mean. Neither statistic is changed to an equally weighted mean over proteins.\n\nBoth assay and protein counts are displayed. With fewer than two proteins, no population interval or test is reported; estimates based on fewer than ten proteins are marked as limited. Intervals are pointwise and are not adjusted for the multiple exploratory comparisons. The two-sided protein-block sign-flip test assumes joint sign symmetry of each protein\'s paired assay contrasts. It is not a Wilcoxon test or a distribution-free test of zero mean.\n')
  if run==2:
   setcell(21,(HERE/'regression_cell.py').read_text())
   setcell(20,'Separate alignment support from structural confidence and assay dynamic range using the same within-assay bins, centered variables and OLS coefficients. Both coverage-based and confidence-based bins are evaluated.\n\nUncertainty uses a protein-cluster sandwich: every bin and assay of one protein stays in the same cluster. The CR1 finite-sample correction counts all absorbed assay intercepts plus the independent covariates, rather than using the smaller rank of the demeaned matrix. Intervals and tests use t(G−1), where G is the number of proteins; these are nominal conditional associations, not causal or independent external confirmation.\n')
  decision_index=20 if run==1 else 23
  original=''.join(n['cells'][decision_index]['source']);main=original.splitlines()[0]
  setcell(decision_index-1,'## 6. Decision and reason\n\nThe pooled and confirmation-partition effects below retain the same point-estimate definitions, with uncertainty now clustered by protein. A positive pooled interval and a positive confirmation estimate do not constitute a complete protocol result. These partitions contain different proteins from the fixed ProteinGym panel, but the reconstruction does not establish the chronology or independence of original axis selection. Comparisons remain exploratory and nominal.\n')
  setcell(decision_index,main+"""
selected=effects[(effects.scheme==MAIN_SCHEME)&(effects.comparison=='AM')]
pooled=selected.loc[selected.subset=='All'].iloc[0]
confirmation=selected.loc[selected.subset=='Confirmation'].iloc[0]
supported=pooled.low>0 and pooled.n_proteins>=10
decision='The pooled protein-cluster interval supports a positive axis association within this panel' if supported else 'The pooled protein-cluster interval does not establish a positive axis association'
if RUN==2 and AXIS==3:
    decision='Alignment support remains a control analysis; these data do not establish a separate independent axis'
display(Markdown(f'**{decision}.** Paired high-minus-low AlphaMissense effect: {pooled["mean"]:.3f} (95% interval {pooled.low:.3f} to {pooled.high:.3f}; {int(pooled.n_assays)} assays, {int(pooled.n_proteins)} proteins). Confirmation-partition effect: {confirmation["mean"]:.3f} (95% interval {confirmation.low:.3f} to {confirmation.high:.3f}; {int(confirmation.n_assays)} assays, {int(confirmation.n_proteins)} proteins).'))
baseline=effects[(effects.subset=='All')&(effects.scheme==MAIN_SCHEME)&effects.comparison.isin(['AM minus BLOSUM','AM minus PSSM'])]
display(baseline)
for row in baseline.itertuples(index=False):
    assessment='a positive paired difference relative to this reference' if row.low>0 and row.n_proteins>=10 else 'no established positive paired difference relative to this reference'
    display(Markdown(f'{row.comparison}: {row.mean:.3f} (95% interval {row.low:.3f} to {row.high:.3f}; {int(row.n_assays)} assays, {int(row.n_proteins)} proteins); {assessment}.'))
if RUN==2 and AXIS==3:
    display(Markdown('Coverage and pLDDT vary together. The protein-clustered adjusted controls quantify the conditional associations after structural confidence and experimental dynamic range are included; this does not establish a separate causal mechanism.'))
""")
 final=len(n['cells'])-1
 export="""# Machine-readable current results are derived from the actual tables above.
def table_records(frame):return json.loads(frame.to_json(orient='records',double_precision=15))
current_results={'analysis_id':ANALYSIS_ID,'cohort':{'variants':len(variants),'assays':int(variants.assay.nunique()),'proteins':int(variants.acc.nunique())},
 'statistical_unit':'protein accession; assay-weighted point estimates retained',
 'decision':decision,'new_inference':False,'audit_fine_tuning':False,
 'scope':'Nominal within-panel estimates using the corrected official-score join; reconstructed splits do not establish independence of original axis selection.'}
if AXIS==2:
    current_results['reported_result']={'control_associations':table_records(depth_controls),'uncertainty':'protein-block percentile bootstrap; Spearman reranked within each draw; no iid p-values'}
    current_results['comparator_contrasts']=[]
else:
    current_results['reported_result']={'main_scheme':MAIN_SCHEME,'primary_contrasts':table_records(selected),'curve_estimates':table_records(curves),'uncertainty':'protein-block percentile bootstrap of the assay-weighted mean; nominal protein-block sign-flip tests assume joint sign symmetry'}
    current_results['comparator_contrasts']=table_records(baseline)
    current_results['all_paired_contrasts']=table_records(effects)
    if RUN==2:current_results['adjusted_controls']=table_records(adjusted)
assert current_results['cohort']=={'variants':273135,'assays':73,'proteins':64},current_results['cohort']
(OUT/'CURRENT_RESULTS.json').write_text(json.dumps(current_results,indent=2,allow_nan=False)+'\\n')
files=[dict(path=str(path.relative_to(OUT)),bytes=path.stat().st_size,sha256=sha256(path)) for path in sorted(OUT.iterdir()) if path.is_file() and path.name!='OUTPUT_MANIFEST.json']
(OUT/'OUTPUT_MANIFEST.json').write_text(json.dumps(files,indent=2)+'\\n')
print('Outputs:',str(OUT.resolve()))
"""

 setcell(final,export)
 p.write_text(json.dumps(n,indent=1,ensure_ascii=False)+'\n')
 print(p.relative_to(R))
