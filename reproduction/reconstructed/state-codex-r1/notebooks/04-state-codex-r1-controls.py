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
wf.source_functions(ROOT,'methods/original/04_analyze_frozen_axis.py',['extract_cell_counts','compute_lfc_scores'])
wf.source_functions(ROOT,'methods/reconstruct.py',['build_condition_table'])
conditions=wf.read_csv(ROOT,'computed/analysis/distance/per_condition_scores.csv')
wf.show_conditions(conditions)


# Cell 6
control_columns=['cell_line','target','identity_lfc_rmse','n_de','log_n_de','n_cells_full','n_cells_all','n_cells','log_n_cells']
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


# Cell 8
wf.source_functions(ROOT,'methods/reconstruct.py',['quintile_matching'])
for axis_name in ['distance','s_phase','lineage']:
    display(Markdown('**'+axis_name+' matching support**'))
    strata=wf.read_csv(ROOT,f'computed/analysis/{axis_name}/matching_strata.csv')
    weights=wf.read_csv(ROOT,f'computed/analysis/{axis_name}/matching_weights.csv')
    display(strata)
    print('Matching observations:',len(weights))
    display(weights.head(5))
display(conditions.groupby(['partition','dose']).agg(rows=('target','size'),targets=('target','nunique'),compounds=('compound','nunique')))


# Cell 10
wf.source_functions(ROOT,'methods/original/04_analyze_frozen_axis.py',['within_design','fit_within'])
wf.source_functions(ROOT,'methods/reconstruct.py',['bootstrap_slopes_fast','analyze_axis'])


# Cell 12
sensitivities=wf.read_csv(ROOT,'computed/analysis/controls/all_sensitivity_estimates.csv')
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


# Cell 14
comparison=wf.historical_comparison(ROOT)
final=wf.read_json(ROOT,'recovery/original_handoff/supporting/results/final_closure_verdict.json')
display(pd.Series(final['primary_candidates'],name='original_agent_decision').to_frame())
print('Historical overall disposition:',final['verdict'])
print('Numerical differences and reconstructed continuation choices remain explicit. No new scientific claim replaces the original determination.')

