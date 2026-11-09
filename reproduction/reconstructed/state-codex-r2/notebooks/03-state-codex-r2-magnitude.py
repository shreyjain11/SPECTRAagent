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
pipeline=wf.run_pipeline(ROOT,'magnitude')
wf.source_functions(ROOT,'methods/replogle.py',['scores','analyze'])
units=wf.read_csv(ROOT,'computed/replogle/magnitude_units.csv')
eligibility=wf.read_csv(ROOT,'computed/replogle/A2_eligibility.csv')
display(units[['context','perturbation','expected_rms','weakness','magnitude_level','state_se']].head(12))
wf.source_receipts(ROOT,['replogle_scores','replogle_analysis','closures'])


# Cell 6
display(JSON(wf.read_json(ROOT,'computed/replogle/magnitude_summary.json')))
display(JSON(wf.read_json(ROOT,'originals/supporting/audit/axis/frozen_axis_A2.json')))


# Cell 8
display(units.groupby(['context','magnitude_level']).agg(units=('perturbation','size'),min_expected_rms=('expected_rms','min'),max_expected_rms=('expected_rms','max')))
display(eligibility)
print('Disjoint candidates:',int(eligibility.confirmation_candidate.sum()))
print('Eligible disjoint candidates:',int(eligibility.confirmation_eligible.sum()))
display(wf.read_csv(ROOT,'computed/replogle/released_condition_availability.csv').head(12))


# Cell 10
wf.source_functions(ROOT,'methods/replogle.py',['de_matrix','row_spearman'])
closures=wf.read_json(ROOT,'computed/closures/closure_diagnostics.json')
display(JSON(closures['A2e']))
display(wf.read_csv(ROOT,'computed/tahoe/cohort.csv').head(12))
display(wf.read_csv(ROOT,'computed/closures/original_public_shard_inventory.csv'))


# Cell 12
wf.source_functions(ROOT,'methods/common.py',['fisher','cluster_fit','curve'])
result=wf.read_json(ROOT,'computed/replogle/magnitude_summary.json')
wf.show_fits(result);display(wf.read_csv(ROOT,'computed/replogle/magnitude_curve.csv'))
wf.show_curve(ROOT,'magnitude_curve.png')
wf.source_functions(ROOT,'methods/closures.py',['run'])


# Cell 14
wf.original_rows(ROOT,['A2','A2e'])
print('Reconstructed: original discovery calculations, release eligibility, Tahoe cohort and resource inventory.')
print('Historical-only partial diagnostics:879mapping count/hash and1536-block progress; original data rows were absent from the handoff.')

