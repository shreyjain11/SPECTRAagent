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
pipeline=wf.run_pipeline(ROOT,'secondary')
wf.source_functions(ROOT,'methods/tahoe.py',['controls'])
wf.source_functions(ROOT,'methods/closures.py',['run'])
secondary=wf.read_csv(ROOT,'computed/closures/secondary_input_axes.csv')
display(secondary.head(12));wf.source_receipts(ROOT,['tahoe_controls','tahoe_analysis','closures'])


# Cell 6
display(wf.read_csv(ROOT,'computed/closures/release_modality_assignments.csv'))
display(JSON(wf.read_json(ROOT,'originals/supporting/audit/axis/frozen_axis_secondary.json')))
display(JSON(wf.read_json(ROOT,'originals/supporting/audit/axis/frozen_axis_A9_mito.json')))


# Cell 8
display(wf.read_csv(ROOT,'computed/closures/support_levels.csv'))
display(secondary[['dose','dose_level']].drop_duplicates().sort_values('dose_level'))
a9=wf.read_csv(ROOT,'computed/tahoe/A9_units.csv')
display(a9.groupby('mito_level').agg(units=('drug','size'),minimum=('mito','min'),maximum=('mito','max')))


# Cell 10
closures=wf.read_json(ROOT,'computed/closures/closure_diagnostics.json')
for name in ['A3','A5','A6']:display(JSON({name:closures[name]}))
display(a9[['context','drug','dose','mito','mito_level','score','n_de','n_treated','n_control','gene_mean','umi_mean']].head(12))


# Cell 12
wf.source_functions(ROOT,'methods/common.py',['fisher','cluster_fit','curve'])
result=wf.read_json(ROOT,'computed/tahoe/A9_summary.json')
wf.show_fits(result);display(wf.read_csv(ROOT,'computed/tahoe/A9_curve.csv'))
wf.show_curve(ROOT,'A9_curve.png')
comparison=wf.read_json(ROOT,'computed/tahoe/historical_comparison.json')
display(pd.DataFrame(comparison).query("analysis == 'A9'"))


# Cell 14
wf.original_rows(ROOT,['A3','A5','A6','A9'])
print('No A3/A5/A6 outcome curve is created; those tests were not performed in the original investigation.')

