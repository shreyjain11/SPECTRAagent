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
pipeline=wf.run_pipeline(ROOT,'dose')
wf.source_functions(ROOT,'methods/tahoe.py',['parse','cohort','controls','scores'])
cohort=wf.read_csv(ROOT,'computed/tahoe/cohort.csv')
display(cohort.head(12));display(JSON(wf.read_json(ROOT,'computed/tahoe/cohort_summary.json')))
wf.source_receipts(ROOT,['tahoe_controls','tahoe_analysis'])


# Cell 6
display(cohort[['dose','weakness','dose_level']].drop_duplicates().sort_values('dose_level'))
display(JSON(wf.read_json(ROOT,'originals/supporting/audit/axis/frozen_axis_A7_dose_official.json')))
display(JSON(wf.read_json(ROOT,'computed/tahoe/A7_contract_diagnostic.json')))
wf.original_rows(ROOT,['A7'])


# Cell 8
for name in ['A8','A10']:
    units=wf.read_csv(ROOT,f'computed/tahoe/{name}_units.csv')
    excluded=wf.read_csv(ROOT,f'computed/tahoe/{name}_excluded_scores.csv')
    display(Markdown('**'+name+' finite measurements**'))
    display(units.groupby(['dose_level','dose']).agg(units=('drug','size'),drugs=('drug','nunique'),contexts=('context','nunique')))
    display(excluded)


# Cell 10
wf.source_functions(ROOT,'methods/tahoe.py',['reference'])
a10=wf.read_csv(ROOT,'computed/tahoe/A10_units.csv')
reference=wf.read_csv(ROOT,'computed/tahoe/basal_reference_scores.csv')
display(a10[['context','drug','dose','score','n_de','n_treated','n_control','reference_score']].head(12))
display(reference.head(12))


# Cell 12
wf.source_functions(ROOT,'methods/common.py',['fisher','cluster_fit','curve'])
for name in ['A8','A10']:
    result=wf.read_json(ROOT,f'computed/tahoe/{name}_summary.json')
    display(Markdown('**'+name+' newly calculated results**'))
    wf.show_fits(result)
    display(pd.Series({k:result[k] for k in ['endpoint','endpoint_ci95','score_exclusions']}).to_frame('calculated'))
    display(wf.read_csv(ROOT,f'computed/tahoe/{name}_curve.csv'))
    wf.show_curve(ROOT,f'{name}_curve.png')
    if name=='A10':display(JSON(result['same_example_reference']))
wf.compare(ROOT,'computed/tahoe/historical_comparison.json')


# Cell 14
wf.original_rows(ROOT,['A7','A8','A10'])
print('Original A10R interpretation: basal reference flat; point-estimate comparison within the documented ±0.02 band.')
print('See notebook04 for the original A9 checkpoint-specific mitochondrial investigation.')

