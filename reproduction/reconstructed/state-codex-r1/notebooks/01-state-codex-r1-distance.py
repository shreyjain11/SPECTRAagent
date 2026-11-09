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
wf.source_functions(ROOT,'methods/original/01_build_prospective_axis.py',['choose_primary_genes','panel_distance'])
mapping=wf.read_csv(ROOT,'computed/features/cell_line_mapping.csv')
primary=wf.read_csv(ROOT,'computed/features/primary_cmp_distances.csv')
independent=wf.read_csv(ROOT,'computed/features/independent_ccle_distances.csv')
display(mapping.head(12));display(primary);display(independent)


# Cell 6
AXIS='distance'
conditions=wf.read_csv(ROOT,f'computed/analysis/{AXIS}/per_condition_scores.csv')
axis=conditions[['cell_line','axis_value','distance_z']].drop_duplicates().sort_values('axis_value')
assert axis.cell_line.is_unique
display(axis)


# Cell 8
levels=axis.copy();levels.insert(0,'level',np.arange(1,len(levels)+1));display(levels)
wf.source_functions(ROOT,'methods/original/04_analyze_frozen_axis.py',['normalize_compound','partition_for'])
wf.source_functions(ROOT,'methods/reconstruct.py',['build_condition_table'])
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
for filename in ['ccle_analysis.json','ccle_exact_contexts_analysis.json']:
    display(Markdown('**Independent-atlas sensitivity:** `'+filename+'`'))
    wf.show_fits(wf.read_json(ROOT,f'computed/analysis/{AXIS}/{filename}'))


# Cell 14
comparison=wf.historical_comparison(ROOT,'distance')
wf.original_decision(ROOT,'basal_transcriptomic_distance','Historical finding: the proposed worsening ran in the opposite direction. The computed raw, adjusted, independent-atlas and control estimates above show the corresponding reconstructed evidence.')

