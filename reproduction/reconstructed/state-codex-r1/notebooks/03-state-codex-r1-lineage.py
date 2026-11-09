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
wf.source_functions(ROOT,'methods/build_features.py',['build_expression'])
mapping=wf.read_csv(ROOT,'computed/features/cell_line_mapping.csv')
lineage=wf.read_csv(ROOT,'computed/features/lineage_features.csv')
display(mapping[['cell_line','lineage']]);display(lineage)


# Cell 6
AXIS='lineage'
conditions=wf.read_csv(ROOT,f'computed/analysis/{AXIS}/per_condition_scores.csv')
axis=conditions[['cell_line','axis_value','distance_z']].drop_duplicates().sort_values('axis_value')
assert axis.cell_line.is_unique
display(axis)


# Cell 8
levels=axis.copy();levels['level']=levels.axis_value.rank(method='dense').astype(int);display(levels)
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
display(Markdown('**ST-HVG discovery direction on the lineage axis**'))
wf.show_fits(wf.read_json(ROOT,f'computed/analysis/{AXIS}/hvg_discovery_analysis.json'))


# Cell 14
comparison=wf.historical_comparison(ROOT,'lineage')
wf.original_decision(ROOT,'training_lineage_scarcity','Historical finding: favorable overall slope and shape, but dose/context instability and opposite discovery direction. Exact operationalization also followed access to the related eval_best checkpoint. The newly computed sensitivities above permit direct comparison with those recorded grounds.')

