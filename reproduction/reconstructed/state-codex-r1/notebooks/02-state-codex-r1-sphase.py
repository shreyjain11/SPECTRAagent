# Cell 2
from pathlib import Path
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


# Cell 4
# Actual source acquisition / verification, input processing, released-score reduction,
# condition-level regressions and curves, even when derived outputs already exist.
wf.run_pipeline(ROOT)
wf.show_receipts(ROOT)
wf.source_functions(ROOT,'methods/build_features.py',['build_obs'])
s_phase=wf.read_csv(ROOT,'computed/features/s_phase_features.csv')
display(s_phase)
plate=wf.read_csv(ROOT,'computed/features/s_score_axis_plate_replication.csv')
qc=wf.read_csv(ROOT,'computed/features/s_phase_qc_filter_sensitivity.csv')
display(plate);display(qc)


# Cell 6
AXIS='s_phase'
conditions=wf.read_csv(ROOT,f'computed/analysis/{AXIS}/per_condition_scores.csv')
axis=conditions[['cell_line','axis_value','distance_z']].drop_duplicates().sort_values('axis_value')
assert axis.cell_line.is_unique
display(axis)


# Cell 8
levels=axis.copy();levels.insert(0,'level',np.arange(1,len(levels)+1));display(levels)
eligibility=wf.read_csv(ROOT,f'computed/analysis/{AXIS}/compound_eligibility.csv')
display(eligibility.head(12));wf.show_conditions(conditions)


# Cell 10
wf.source_functions(ROOT,'methods/original/04_analyze_frozen_axis.py',['compute_lfc_scores'])
wf.show_conditions(conditions)


# Cell 12
wf.source_functions(ROOT,'methods/original/04_analyze_frozen_axis.py',['within_design','fit_within','context_spc'])
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
display(Markdown('**ST-HVG discovery analysis on the same source-built S-phase axis**'))
wf.show_fits(wf.read_json(ROOT,f'computed/analysis/{AXIS}/hvg_discovery_analysis.json'))


# Cell 14
comparison=wf.historical_comparison(ROOT,'s_phase')
from scipy.stats import spearmanr
xcol='axis_value' if 'axis_value' in curve else 'distance'
rho=float(spearmanr(curve[xcol],curve.state_rmse_mean).statistic)
print('Recomputed five-context curve Spearman rho:',rho)
print('Original documented shape threshold: 0.70; reconstructed shape passes:',rho>=0.70)
wf.original_decision(ROOT,'baseline_s_phase_score_heterogeneity','Historical finding: strong adjusted regression with stable continuous controls, but the original context-ordering requirement failed. The analysis and curve above are the newly calculated evidence.')

