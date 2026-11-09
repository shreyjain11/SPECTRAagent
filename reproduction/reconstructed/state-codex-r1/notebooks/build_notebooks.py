"""Build the four source-to-decision notebooks (no scientific execution here)."""
from pathlib import Path
import nbformat as nbf

OUT=Path(__file__).resolve().parent
STAGES=['Data acquisition','Processing','Axis','Levels and eligibility','Model / released scores','Regressions, curves and controls','Historical result and decision']

def md(text): return nbf.v4.new_markdown_cell(text)
def code(text): return nbf.v4.new_code_cell(text.strip()+'\n')
def section(cells,n,text,source=None):
    cells.append(md(f'## {n}. {STAGES[n-1]}\n\n{text}'))
    if source: cells.append(code(source))

BOOT='''from pathlib import Path
import importlib.util, json, sys
import numpy as np
import pandas as pd
from IPython.display import display, Markdown, JSON
ROOT=next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'methods/sources.json').is_file())
spec=importlib.util.spec_from_file_location('state_notebook_workflow',ROOT/'notebooks/shared.py')
wf=importlib.util.module_from_spec(spec);spec.loader.exec_module(wf)
INPUTS=ROOT/'inputs'
FEATURES=ROOT/'computed/features'
ANALYSIS=ROOT/'computed/analysis'
pd.set_option('display.max_colwidth',100)
pd.set_option('display.max_rows',100)
source_manifest=json.loads((ROOT/'methods/sources.json').read_text())
source_rows=pd.DataFrame(source_manifest['inputs']).drop_duplicates('path')
display(source_rows[['path','bytes','sha256','url']])
print('Unique public source files:',len(source_rows))
print('Declared source bytes:',int(source_rows.bytes.sum()))
print('Run All recalculates features, released-score errors and analyses below. Existing public downloads are reused only after checksum verification.')
'''
PIPELINE='''# Actual source acquisition / verification, input processing, released-score reduction,
# condition-level regressions and curves, even when derived outputs already exist.
wf.run_pipeline(ROOT)
wf.show_receipts(ROOT)
'''
SOURCE='''**Run All executes the complete source → input features → released-score metrics → condition-level analysis → curves chain.** The four notebooks share source downloads, but default Run All **recalculates** derived features, released-score errors and all analyses even if computed tables exist. Original public inputs are downloaded if absent and checksum verified before reuse. The separate pipeline CLI offers `--reuse-computed` only for deliberately requested receipt-verified reuse; these notebook defaults do not use it. A cold run requires the documented environment, network access, disk space and CPU time; execute on exxact05 for this reconstruction.

The model outputs are the original released STATE predictions. Recomputing their per-condition full-feature log2-fold-change RMSE requires no new neural inference. Archived five-context means and fitted summaries are comparison targets only; they do not enter the calculations below.

Surviving original methods are preserved byte-for-byte. Continuation methods are reconstructed from the original report and native commands. The declared bootstrap seed, axis-standardization population and quintile-matching implementation are recorded explicitly; they were not selected by fitting the historical answers. See [method details](../methods/METHODS.md), [source manifest](../methods/sources.json), [pipeline](../methods/run_pipeline.py), and [original report](../recovery/original_handoff/REPORT.md).'''

def start(title): return [md('# '+title+'\n\n'+SOURCE)]
def save(filename,cells,axis):
    nb=nbf.v4.new_notebook(cells=cells)
    nb.metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python'},'state_reconstruction':{'axis':axis,'chain':STAGES,'default_execution':'actual_source_pipeline_recalculation','historical_aggregates':'validation_targets_only','scientific_execution_host':'exxact05','new_model_inference':False}}
    nbf.validate(nb);nbf.write(nb,OUT/filename)
    (OUT/filename.replace('.ipynb','.py')).write_text('\n\n'.join(f'# Cell {i}\n{c.source}' for i,c in enumerate(cells) if c.cell_type=='code')+'\n')
    print(filename,len(cells),'cells')

SCORE_CODE='''wf.source_functions(ROOT,'methods/original/04_analyze_frozen_axis.py',['compute_lfc_scores'])
wf.show_conditions(conditions)
'''
FIT_CODE='''wf.source_functions(ROOT,'methods/original/04_analyze_frozen_axis.py',['within_design','fit_within','context_spc'])
wf.source_functions(ROOT,'methods/reconstruct.py',['bootstrap_slopes_fast','quintile_matching'])
analysis=wf.read_json(ROOT,f'computed/analysis/{AXIS}/analysis.json')
display(JSON(analysis['policy']))
display(pd.Series(analysis['computed_diagnostics'],name='recomputed_diagnostic').to_frame())
print('Main displayed fits: confirmation partition; discovery/all fits remain in analysis.json.')
fits=wf.show_fits(analysis['partitions']['confirmation'])
curve=wf.read_csv(ROOT,f'computed/analysis/{AXIS}/spc_table.csv')
display(curve)
wf.show_curve(ROOT,AXIS)
strata=wf.read_csv(ROOT,f'computed/analysis/{AXIS}/matching_strata.csv')
weights=wf.read_csv(ROOT,f'computed/analysis/{AXIS}/matching_weights.csv')
display(strata)
print('Matching rows:',len(weights),'— inspect full assignment/weights in the linked CSV.')
display(weights.head(10))
'''

c=start('STATE Codex r1 — 01 Basal transcriptomic distance')
section(c,1,'The manifest pins the CMP expression archive, DepMap 23Q4 metadata/expression, original training-context map, Tahoe cell metadata and official ST-HVG `eval_best` prediction/observation files. SHA-256 verification happens before use. Source downloads can be reused after checksum verification; each notebook default recalculates its shared derived stages.',BOOT)
section(c,2,'The pipeline applies the original atlas method to source matrices and computes actual released-score errors. The original code selects 2,000 high-variance genes from mapped training contexts, applies training mean/sample-SD standardization, and takes the median of five nearest RMS distances. This follows the code’s actual gene selection; no extra gene filter is added from prose.',PIPELINE+'''wf.source_functions(ROOT,'methods/original/01_build_prospective_axis.py',['choose_primary_genes','panel_distance'])
mapping=wf.read_csv(ROOT,'computed/features/cell_line_mapping.csv')
primary=wf.read_csv(ROOT,'computed/features/primary_cmp_distances.csv')
independent=wf.read_csv(ROOT,'computed/features/independent_ccle_distances.csv')
display(mapping.head(12));display(primary);display(independent)
''')
section(c,3,'The axis is reconstructed entirely from reference expression and the training-context mapping. Independent CCLE distance is computed separately, including the explicitly documented parental HepG2 proxy. These values then join the per-condition scores.', '''AXIS='distance'
conditions=wf.read_csv(ROOT,f'computed/analysis/{AXIS}/per_condition_scores.csv')
axis=conditions[['cell_line','axis_value','distance_z']].drop_duplicates().sort_values('axis_value')
assert axis.cell_line.is_unique
display(axis)
''')
section(c,4,'Near-to-far levels follow the calculated input-side axis. Drug-dose targets must occur in all five contexts, and parent compounds need at least two doses. The original SHA-256 parent-compound partition keeps all contexts/doses together. Eligibility is calculated from the real released rows, not forced to the historical count.', '''levels=axis.copy();levels.insert(0,'level',np.arange(1,len(levels)+1));display(levels)
wf.source_functions(ROOT,'methods/original/04_analyze_frozen_axis.py',['normalize_compound','partition_for'])
wf.source_functions(ROOT,'methods/reconstruct.py',['build_condition_table'])
eligibility=wf.read_csv(ROOT,f'computed/analysis/{AXIS}/compound_eligibility.csv')
display(eligibility.head(12));wf.show_conditions(conditions)
''')
section(c,5,'The original full-feature scorer aligns released observed/predicted feature rows and evaluates log2 fold changes. STATE RMSE is `sqrt(mean((predicted − observed)²))`; the no-effect reference is `sqrt(mean(observed²))`. Observed FDR<0.05 yields the DE count; cell counts supply the same-example adjustment. The following code and condition rows are the actual calculation route.',SCORE_CODE)
section(c,6,'Raw and adjusted regressions use within-drug-dose centering and parent-compound clustered inference. Target and reference bootstrap draws use the same compound multiplicities. Curves first average doses within parent compound/context and then weight compounds equally. Error bars are recomputed from those compound observations. Matching, dose strata, leave-one-context-out and independent-atlas fits are also executed; the declared reconstructed matching rule remains labeled.',FIT_CODE+'''for filename in ['ccle_analysis.json','ccle_exact_contexts_analysis.json']:
    display(Markdown('**Independent-atlas sensitivity:** `'+filename+'`'))
    wf.show_fits(wf.read_json(ROOT,f'computed/analysis/{AXIS}/{filename}'))
''')
section(c,7,'Compare the newly calculated coefficients/curves with the recorded result. The original agent rejected this candidate because STATE error decreased with greater distance, including adjusted and sensitivity fits. Any numerical reconstruction difference remains visible rather than changing the input panel or method to obtain the original answer.', '''comparison=wf.historical_comparison(ROOT,'distance')
wf.original_decision(ROOT,'basal_transcriptomic_distance','Historical finding: the proposed worsening ran in the opposite direction. The computed raw, adjusted, independent-atlas and control estimates above show the corresponding reconstructed evidence.')
''')
save('01-state-codex-r1-distance.ipynb',c,'distance')

c=start('STATE Codex r1 — 02 Baseline S-phase-score heterogeneity')
section(c,1,'Sources are original Tahoe untreated-cell metadata (`drug == DMSO_TF`) and the pinned official ST-SE `eval_best` prediction/observation release. The original ST-HVG discovery partition is processed separately. No stored context mean serves as a replacement for per-cell features or released per-condition outcomes.',BOOT)
section(c,2,'The shared pipeline reads the actual metadata and computes sample SD of S score for each context, plate parity and QC subset; it also reconstructs condition cell counts. The native commands establish the all-cell and odd/even plate calculations. The full-QC check is a separate sensitivity.',PIPELINE+'''wf.source_functions(ROOT,'methods/build_features.py',['build_obs'])
s_phase=wf.read_csv(ROOT,'computed/features/s_phase_features.csv')
display(s_phase)
plate=wf.read_csv(ROOT,'computed/features/s_score_axis_plate_replication.csv')
qc=wf.read_csv(ROOT,'computed/features/s_phase_qc_filter_sensitivity.csv')
display(plate);display(qc)
''')
section(c,3,'The input-side axis is within-context heterogeneity of baseline S score, not mean S score or model error. Its values come from the untreated cells. Outcome measurements are joined only after the feature calculation.', '''AXIS='s_phase'
conditions=wf.read_csv(ROOT,f'computed/analysis/{AXIS}/per_condition_scores.csv')
axis=conditions[['cell_line','axis_value','distance_z']].drop_duplicates().sort_values('axis_value')
assert axis.cell_line.is_unique
display(axis)
''')
section(c,4,'Levels 1–5 are assigned by increasing reconstructed baseline sample SD. The original compound partition and five-context/two-dose eligibility rules are applied to the detailed released rows. The odd/even and full-QC feature tables above show measurement-order robustness independently of prediction error.', '''levels=axis.copy();levels.insert(0,'level',np.arange(1,len(levels)+1));display(levels)
eligibility=wf.read_csv(ROOT,f'computed/analysis/{AXIS}/compound_eligibility.csv')
display(eligibility.head(12));wf.show_conditions(conditions)
''')
section(c,5,'ST-SE `eval_best` predictions are scored against the original observed full-feature log2 fold changes. The fixed no-effect reference uses the identical observed rows. The table below includes actual per-target error, DE and observed-cell measurements; all further regressions consume these values.',SCORE_CODE)
section(c,6,'The main curve and uncertainty are recomputed from parent-compound observations. The analysis includes raw/adjusted and paired-reference slopes, dose and leave-context controls, explicitly reconstructed quintile matching, plus the ST-HVG discovery calculation. The displayed plate/QC replication above comes from original cells rather than saved SD values.',FIT_CODE+'''display(Markdown('**ST-HVG discovery analysis on the same source-built S-phase axis**'))
wf.show_fits(wf.read_json(ROOT,f'computed/analysis/{AXIS}/hvg_discovery_analysis.json'))
''')
section(c,7,'The historical decision separated a strong adjusted positive association from a non-monotonic five-context curve. The report recorded Spearman rho 0.30 against its frozen 0.70 threshold. Here the curve, correlation and regression evidence are recalculated; the original disposition is retained as history.', '''comparison=wf.historical_comparison(ROOT,'s_phase')
from scipy.stats import spearmanr
xcol='axis_value' if 'axis_value' in curve else 'distance'
rho=float(spearmanr(curve[xcol],curve.state_rmse_mean).statistic)
print('Recomputed five-context curve Spearman rho:',rho)
print('Original documented shape threshold: 0.70; reconstructed shape passes:',rho>=0.70)
wf.original_decision(ROOT,'baseline_s_phase_score_heterogeneity','Historical finding: strong adjusted regression with stable continuous controls, but the original context-ordering requirement failed. The analysis and curve above are the newly calculated evidence.')
''')
save('02-state-codex-r1-sphase.ipynb',c,'s_phase')

c=start('STATE Codex r1 — 03 Training-lineage scarcity')
section(c,1,'The feature sources are the original training-context map and DepMap 23Q4 lineage labels. The outcome source is official ST-SE `eval_last`; ST-HVG discovery rows provide the separate direction check. This reconstructs the actual published output analysis without new model inference.',BOOT)
section(c,2,'Training contexts are mapped from the original source metadata and counted within each held-out context’s DepMap lineage. The counts are calculated from membership, not copied from reported numbers. The code then applies `−log(1 + count)`.',PIPELINE+'''wf.source_functions(ROOT,'methods/build_features.py',['build_expression'])
mapping=wf.read_csv(ROOT,'computed/features/cell_line_mapping.csv')
lineage=wf.read_csv(ROOT,'computed/features/lineage_features.csv')
display(mapping[['cell_line','lineage']]);display(lineage)
''')
section(c,3,'Increasing lineage scarcity means fewer mapped training contexts in the same lineage. The feature is built before its join to `eval_last` score measurements. The two pancreatic contexts share one feature value; the tie is preserved.', '''AXIS='lineage'
conditions=wf.read_csv(ROOT,f'computed/analysis/{AXIS}/per_condition_scores.csv')
axis=conditions[['cell_line','axis_value','distance_z']].drop_duplicates().sort_values('axis_value')
assert axis.cell_line.is_unique
display(axis)
''')
section(c,4,'Dense ranks define four distinct scarcity levels across the five held-out contexts. The same compound hashing and eligibility rules govern discovery and confirmation; the context shape uses five means with the pancreatic tie rather than pooling to four lineage means.', '''levels=axis.copy();levels['level']=levels.axis_value.rank(method='dense').astype(int);display(levels)
eligibility=wf.read_csv(ROOT,f'computed/analysis/{AXIS}/compound_eligibility.csv')
display(eligibility.head(12));wf.show_conditions(conditions)
''')
section(c,5,'Recompute original full-feature STATE and identity-reference LFC RMSE from the `eval_last` released rows. Condition-level DE and observed-cell measurements enter the adjustment; no archived adjusted estimate is supplied to the fitter.',SCORE_CODE)
section(c,6,'The curve, clustered fits, paired reference comparison and compound-bootstrap intervals are calculated from the rebuilt condition table. Dose-specific and leave-context fits expose the original instability checks, while the separate ST-HVG discovery calculation tests the historical direction disagreement.',FIT_CODE+'''display(Markdown('**ST-HVG discovery direction on the lineage axis**'))
wf.show_fits(wf.read_json(ROOT,f'computed/analysis/{AXIS}/hvg_discovery_analysis.json'))
''')
section(c,7,'The original agent rejected this follow-up after the 5 µM estimate weakened, removing HepG2/C3A reversed the adjusted direction, and ST-HVG discovery disagreed. Its related-checkpoint timing is a historical qualification, not something inferred from these numerical results. Rebuilt values and differences are shown explicitly.', '''comparison=wf.historical_comparison(ROOT,'lineage')
wf.original_decision(ROOT,'training_lineage_scarcity','Historical finding: favorable overall slope and shape, but dose/context instability and opposite discovery direction. Exact operationalization also followed access to the related eval_best checkpoint. The newly computed sensitivities above permit direct comparison with those recorded grounds.')
''')
save('03-state-codex-r1-lineage.ipynb',c,'lineage')

c=start('STATE Codex r1 — 04 Effect, cell-count and dose controls')
section(c,1,'Controls use the same verified original released predicted/observed DE rows and Tahoe metadata as the three candidate analyses. Baseline input-side candidate screens also use the original untreated-cell metadata. This notebook recalculates the shared chain, then inspects actual per-condition controls and their fitted sensitivities.',BOOT)
section(c,2,'The scorer computes identity-reference RMSE (true perturbation magnitude), observed FDR-based DE counts and observed cell counts. The original rule uses full-QC cell counts when positive and falls back to all observed cells when there are zero full-QC cells. Target parsing, compound hashing and complete-panel eligibility are shared with the main analyses.',PIPELINE+'''wf.source_functions(ROOT,'methods/original/04_analyze_frozen_axis.py',['extract_cell_counts','compute_lfc_scores'])
wf.source_functions(ROOT,'methods/reconstruct.py',['build_condition_table'])
conditions=wf.read_csv(ROOT,'computed/analysis/distance/per_condition_scores.csv')
wf.show_conditions(conditions)
''')
section(c,3,'Identity RMSE, log1p DE count and log1p observed cell count are controls/re-attribution variables, not relabeled input-side failure axes. Baseline candidate screens are reconstructed from the measured metadata and the discovery outcome partition; their diagnostic results are displayed separately.', '''control_columns=['cell_line','target','identity_lfc_rmse','n_de','log_n_de','n_cells_full','n_cells_all','n_cells','log_n_cells']
display(conditions[control_columns].head(12))
counts=wf.read_csv(ROOT,'computed/analysis/controls/source_axis_counts.csv')
screen=wf.read_csv(ROOT,'computed/analysis/controls/baseline_discovery_screen.csv')
display(counts);display(screen)
baseline=wf.read_csv(ROOT,'computed/analysis/controls/baseline_discovery_features.csv')
display(baseline)
import matplotlib.pyplot as plt
feature_names=['gene_mean','gene_sd','tscp_mean','tscp_sd','mito_mean','mito_sd','S_sd','G2M_sd','phase_entropy']
fig,axes=plt.subplots(3,3,figsize=(12,10),layout='constrained')
for ax,feature in zip(axes.flat,feature_names):
    ax.scatter(baseline[feature],baseline.state_rmse_discovery,color='#315b78')
    for row in baseline.itertuples():
        ax.annotate(row.cell_line,(getattr(row,feature),row.state_rmse_discovery),xytext=(3,3),textcoords='offset points',fontsize=6)
    ax.set(xlabel=feature,ylabel='HVG discovery mean LFC RMSE')
    ax.spines[['top','right']].set_visible(False)
fig.suptitle('Nine original baseline feature screens — recomputed from cells and released scores')
wf.show_figure(fig);plt.close(fig)
''')
section(c,4,'Actual sensitivity strata include effect/cell-count quintiles, the three released dose levels, and each held-out-context exclusion. The historically named matching sensitivity uses effect and cell-count quintile indicators in the original within-target regression, preserving all eligible observations. The original saved fit records the eight indicator names; cutpoints within the analysis partition are a declared reconstruction choice. Assignment tables show the actual terms entering the fit.', '''wf.source_functions(ROOT,'methods/reconstruct.py',['quintile_matching'])
for axis_name in ['distance','s_phase','lineage']:
    display(Markdown('**'+axis_name+' matching support**'))
    strata=wf.read_csv(ROOT,f'computed/analysis/{axis_name}/matching_strata.csv')
    weights=wf.read_csv(ROOT,f'computed/analysis/{axis_name}/matching_weights.csv')
    display(strata)
    print('Matching observations:',len(weights))
    display(weights.head(5))
display(conditions.groupby(['partition','dose']).agg(rows=('target','size'),targets=('target','nunique'),compounds=('compound','nunique')))
''')
section(c,5,'The model/reference errors are scored on the same feature rows. Continuous-control models then fit actual condition observations with within-target centering and parent-compound clustered inference. The source below shows the fit, rather than substituting a reported coefficient or inferring a regression from five means.', '''wf.source_functions(ROOT,'methods/original/04_analyze_frozen_axis.py',['within_design','fit_within'])
wf.source_functions(ROOT,'methods/reconstruct.py',['bootstrap_slopes_fast','analyze_axis'])
''')
section(c,6,'The following table contains newly calculated raw/adjusted, matching, dose, exclusion and reference checks across the three analyses. Each estimate traces to the detailed source-built condition table. The plot is rendered from that computed table; it is not a plot of retained original fit summaries.', '''sensitivities=wf.read_csv(ROOT,'computed/analysis/controls/all_sensitivity_estimates.csv')
display(sensitivities)
control_analysis=wf.read_json(ROOT,'computed/analysis/controls/analysis.json')
wf.show_fits(control_analysis['axes'])
wf.show_curve(ROOT,'controls')
sensitivities=sensitivities.loc[sensitivities.partition.eq('confirmation')].copy()
import matplotlib.pyplot as plt
if 'estimate' not in sensitivities: raise ValueError('Calculated sensitivity table lacks estimate')
labels=sensitivities.drop(columns=[c for c in sensitivities if c not in ['axis','partition','kind','subset','analysis','dose','excluded_context','model']]).astype(str).agg(' / '.join,axis=1)
if labels.empty: labels=sensitivities.index.astype(str)
fig,ax=plt.subplots(figsize=(10,max(5,len(sensitivities)*.22)))
ax.scatter(sensitivities.estimate,np.arange(len(sensitivities)),color='#315b78',s=20)
ax.axvline(0,color='gray',linewidth=1)
ax.set(yticks=np.arange(len(sensitivities)),yticklabels=labels,xlabel='Recomputed slope per axis SD',title='Recomputed confirmation dose and leave-context sensitivities')
ax.invert_yaxis();ax.spines[['top','right']].set_visible(False);fig.tight_layout()
wf.show_figure(fig);plt.close(fig)
''')
section(c,7,'The original agent used these diagnostics to distinguish a negative distance trend, a strong but non-monotonic S-phase association, and an unstable lineage follow-up. Effect magnitude, DE count, cell count and dose remained controls. The table below compares rebuilt numbers with historical targets without treating those targets as observations.', '''comparison=wf.historical_comparison(ROOT)
final=wf.read_json(ROOT,'recovery/original_handoff/supporting/results/final_closure_verdict.json')
display(pd.Series(final['primary_candidates'],name='original_agent_decision').to_frame())
print('Historical overall disposition:',final['verdict'])
print('Numerical differences and reconstructed continuation choices remain explicit. No new scientific claim replaces the original determination.')
''')
save('04-state-codex-r1-controls.ipynb',c,'controls')
