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
pipeline=wf.run_pipeline(ROOT,'modality')
wf.source_functions(ROOT,'methods/closures.py',['run'])
assignments=wf.read_csv(ROOT,'computed/closures/release_modality_assignments.csv')
display(assignments);wf.source_receipts(ROOT,['closures'])


# Cell 6
display(pd.crosstab(assignments.dataset,assignments.modality))
display(assignments[['dataset','modality','model','representation','setting']].drop_duplicates())


# Cell 8
dataset=(assignments.dataset=='Tahoe').astype(int)
modality=(assignments.modality=='chemical drug').astype(int)
design=pd.DataFrame({'intercept':1,'Tahoe_dataset':dataset,'chemical_modality':modality})
display(design)
assert np.array_equal(dataset,modality)


# Cell 10
diagnostic=wf.read_json(ROOT,'computed/closures/closure_diagnostics.json')['A4']
display(JSON(diagnostic))
assert diagnostic['outcome_test_performed'] is False


# Cell 12
calculated_rank=int(np.linalg.matrix_rank(design.to_numpy(float)))
assert calculated_rank==diagnostic['design_rank']
display(pd.DataFrame([{'design_columns':design.shape[1],'recomputed_rank':calculated_rank,'dataset_equals_modality':bool(np.array_equal(dataset,modality))}]))


# Cell 14
wf.original_rows(ROOT,['A4'])
print('No modality performance curve or outcome coefficient was originally estimated; this notebook reproduces the source-design diagnostic instead.')

