"""Rerun the corrected plot cell from public retained individual measurements."""
import json,hashlib,os,re,sys
from pathlib import Path
import nbformat
import numpy as np
from nbclient import NotebookClient
ROOT=Path(__file__).resolve().parents[3]
NOTEBOOK=ROOT/'inline/state/state-codex-r1/test-04.ipynb'
SOURCE=ROOT/'reconstructed/state-codex-r1/computed/analysis/controls/per_condition_scores.csv'
OUTPUT=Path(sys.argv[1]).resolve();OUTPUT.mkdir(parents=True,exist_ok=True)
b=nbformat.read(NOTEBOOK,as_version=4)
source=b.cells[21].source.replace("xlabel='Perturbation magnitude, DE count, cell count and dose'", "xlabel='Baseline S-phase-score standard deviation'").replace("title='STATE Codex R1 controls — confirmation compounds'", "title='S-phase heterogeneity and ST-HVG error — confirmation compounds'")
setup=f'''from pathlib import Path
from io import BytesIO
import numpy as np,pandas as pd
from scipy.stats import spearmanr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from IPython.display import display,Image
OUTPUT_DIR=Path({str(OUTPUT)!r})
BOOTSTRAP_REPS,RANDOM_SEED=10000,20260714
records=pd.read_csv({str(SOURCE)!r},low_memory=False)
sphase=records[records.axis.eq('s_phase')].groupby('cell_line').S_sd.first()
confirm=records[records.axis.eq('distance') & records.run.eq('hvg_best') & records.partition.eq('confirmation')].copy()
confirm['distance']=confirm.cell_line.map(sphase)
assert confirm.distance.notna().all()
assert not confirm.duplicated(['cell_line','target']).any()
assert len(confirm)==4020
'''
runner=nbformat.v4.new_notebook(cells=[nbformat.v4.new_code_cell(setup),nbformat.v4.new_code_cell(source),nbformat.v4.new_code_cell("curve.to_csv(OUTPUT_DIR/'corrected_curve.csv',index=False)")])
NotebookClient(runner,timeout=300,kernel_name='python3',resources={'metadata':{'path':str(OUTPUT)}}).execute()
# Assert numerical identity at the precision printed in the previous notebook.
import pandas as pd
from io import StringIO
from bs4 import BeautifulSoup
old_table=next(o.data['text/html'] for o in b.cells[21].outputs if o.output_type=='display_data' and 'text/html' in o.data)
old=pd.read_html(StringIO(old_table))[0]
if old.columns[0].startswith('Unnamed'):old=old.drop(columns=old.columns[0])
new=pd.read_csv(OUTPUT/'corrected_curve.csv')
old=old.set_index('cell_line').sort_index();new=new.set_index('cell_line').sort_index()
assert old.index.equals(new.index)
checks=[]
for col in old.columns:
 x=pd.to_numeric(old[col],errors='coerce').to_numpy(float);y=pd.to_numeric(new[col],errors='coerce').to_numpy(float)
 np.testing.assert_allclose(x,y,atol=5.1e-7,rtol=0,equal_nan=True)
 checks.append({'column':col,'max_abs_difference':float(np.nanmax(np.abs(x-y))) if np.isfinite(x-y).any() else None})
b.cells[21]=runner.cells[1]
b.cells[18].source='''## 5. Curves and controls

Within-target regressions compare contexts for the same compound and dose. Continuous controls are no-effect RMSE, log(1 + significant-gene count), and log(1 + cell count). Confidence intervals resample compounds 10,000 times; paired fits use the same draws. Context curves first average doses within each compound, then weight compounds equally.

The first figure shows baseline S-phase-score standard deviation against ST-HVG error in confirmation compounds. The later panels separately show response magnitude, DE count, cell count and dose. These diagnostics do not establish an independently confirmed degradation axis.
'''
nbformat.write(b,NOTEBOOK)
nbformat.write(runner,OUTPUT/'executed_plot_correction.ipynb')
(OUTPUT/'numerical_check.json').write_text(json.dumps({'input':str(SOURCE.relative_to(ROOT)),'input_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'rows':4020,'executed_notebook_cells':[21],'max_allowed_display_rounding_error':5.1e-7,'checks':checks},indent=2)+'\n')
print('Recomputed plot agrees with all retained plotted numbers at original display precision.')
