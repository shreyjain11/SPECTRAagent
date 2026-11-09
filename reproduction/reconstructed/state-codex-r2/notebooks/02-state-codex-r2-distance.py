# Cell 2
from pathlib import Path
import importlib.util,json,sys
import numpy as np
import pandas as pd
from IPython.display import display,JSON,Markdown
ROOT=next(p for p in [Path.cwd(),*Path.cwd().parents] if (p/'methods/replogle.py').is_file() and (p/'originals/REPORT.md').is_file())
spec=importlib.util.spec_from_file_location('state_codex_r2_notebook',ROOT/'notebooks/shared.py')
wf=importlib.util.module_from_spec(spec);spec.loader.exec_module(wf)
pd.set_option('display.max_colwidth',100);pd.set_option('display.max_rows',100)
manifest=wf.read_json(ROOT,'methods/sources.json')
sources=pd.DataFrame(manifest['inputs'])
display(sources[['path','bytes','sha256','url']])
if manifest.get('remote_observations'):
    display(Markdown('**Pinned observation-only source objects used for Replogle cell counts**'))
    display(pd.DataFrame(manifest['remote_observations']))
wf.source_functions(ROOT,'methods/acquire.py',['main'])
print('Manifest public input records:',len(sources))
print('The next cell executes actual source calculation for this investigation.')


# Cell 4
pipeline=wf.run_pipeline(ROOT,'distance')
wf.source_functions(ROOT,'methods/replogle.py',['axes','de_matrix','row_spearman'])
axis=wf.read_csv(ROOT,'computed/replogle/axis.csv')
display(axis);display(JSON(wf.read_json(ROOT,'computed/replogle/axis_summary.json')))
wf.source_receipts(ROOT,['replogle_axis','replogle_scores','replogle_observations','replogle_analysis'])


# Cell 6
display(axis[['context','nearest_distance','distance','hpa_distance','hpa_e61_distance']])
print('Calculated nearest distinct values:',axis.nearest_distance.round(12).nunique())
print('Calculated panel-mean distinct values:',axis.distance.round(12).nunique())
display(JSON(wf.read_json(ROOT,'originals/supporting/audit/axis/frozen_axis.json')))
wf.original_rows(ROOT,['A1a'])


# Cell 8
display(axis.sort_values('level'))
display(JSON(wf.read_json(ROOT,'computed/replogle/score_summary.json')))
units=wf.read_csv(ROOT,'computed/replogle/distance_units.csv')
display(units.groupby('context').agg(units=('perturbation','size'),perturbations=('perturbation','nunique')))


# Cell 10
wf.source_functions(ROOT,'methods/replogle.py',['scores'])
wf.source_functions(ROOT,'methods/observation_controls.py',['run'])
display(units[['context','perturbation','distance','state_se','state_hvg','reference','effect_rms','n_de','n_treated','n_control']].head(12))


# Cell 12
wf.source_functions(ROOT,'methods/common.py',['fisher','cluster_fit','curve'])
result=wf.read_json(ROOT,'computed/replogle/distance_summary.json')
wf.show_fits(result);display(JSON(result['exact_context_permutation']))
display(wf.read_csv(ROOT,'computed/replogle/distance_curve.csv'))
wf.show_curve(ROOT,'distance_curve.png')
wf.compare(ROOT,'computed/replogle/historical_comparison.json')


# Cell 14
wf.original_rows(ROOT,['A1a','A1b'])
print('The isolated RPE1 endpoint was not the original distance-axis finding; the whole frozen ordering was evaluated.')

