"""Separate original formula on current rows from rounded historical displays."""
import os
os.environ.setdefault('MPLCONFIGDIR','/private/tmp/am-independent-mpl')
import io,json,pathlib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import spearmanr,wilcoxon
P=pathlib.Path(__file__).resolve().parent.parent
BASE=P/'alphamissense';OWN=P/'independent/original-on-current';OWN.mkdir(exist_ok=True)
reports=[]
for folder in sorted((BASE/'outputs').glob('am-opus-r*-test-*')):
 if not (folder/'CURRENT_RESULTS.json').exists():continue
 ident=folder.name;run=int(ident.split('-')[2][1:]);number=int(ident.rsplit('-',1)[1]);own=OWN/ident;own.mkdir(exist_ok=True)
 old=json.loads((BASE/'before'/ident/f'test-{number:02d}.ipynb').read_text())
 ns={'np':np,'pd':pd,'plt':plt,'wilcoxon':wilcoxon,'spearmanr':spearmanr,'RUN':run,'OUT':own,'AXIS_LABEL':'Axis','show_figure':lambda f:plt.close(f),'display':lambda *args:None}
 if number==2:
  ns['accuracy']=pd.read_csv(folder/'assay_performance.csv');cell=14;tables=[('depth_controls.csv',['subset'],'rho','n_assays')]
 else:
  ns['scores']=pd.read_csv(folder/'assay_level_scores.csv');cell=18 if run==1 else 19
  ns['LEVEL_LABELS']={s:[str(l) for l in sorted(g.level.unique())] for s,g in ns['scores'].groupby('scheme')}
  tables=[('curves.csv',['scheme','method','level'],'mean','n_assays'),('paired_effects.csv',['subset','scheme','comparison'],'mean','n_assays')]
 exec(compile(''.join(old['cells'][cell]['source']),str(BASE/'before'/ident/f'cell{cell}'),'exec'),ns)
 result={'analysis_id':ident,'original_formula_on_current_rows':[],'historical_display_comparison':[]}
 for filename,keys,value,count in tables:
  orig=pd.read_csv(own/filename).set_index(keys);new=pd.read_csv(folder/filename).set_index(keys);merged=orig[[value,count]].join(new[[value,count]],lsuffix='_original',rsuffix='_corrected');assert len(merged)==len(orig)==len(new)
  diff=abs(merged[value+'_original']-merged[value+'_corrected']);assert diff.max()<1e-14;assert(merged[count+'_original']==merged[count+'_corrected']).all()
  result['original_formula_on_current_rows'].append({'table':filename,'rows':len(merged),'max_absolute_point_difference':float(diff.max()),'eligible_assay_counts_identical':True})
  for output in old['cells'][cell]['outputs']:
   html=output.get('data',{}).get('text/html')
   if not html:continue
   for table in pd.read_html(io.StringIO(''.join(html))):
    if not set(keys+[value]).issubset(table.columns):continue
    # Every displayed row that retains its numeric value is compared; ellipses remain excluded.
    table[value]=pd.to_numeric(table[value],errors='coerce');table=table[table[value].notna()].copy()
    for key in keys:
     if key=='level':table[key]=pd.to_numeric(table[key])
    current=pd.read_csv(folder/filename);joined=table[keys+[value]].merge(current[keys+[value]],on=keys,suffixes=('_historical_display','_fresh'))
    joined['difference']=joined[value+'_fresh']-joined[value+'_historical_display']
    joined.to_csv(own/(filename.replace('.csv','-historical-display-comparison.csv')),index=False)
    i=joined.difference.abs().idxmax();row=joined.loc[i]
    result['historical_display_comparison'].append({'table':filename,'displayed_numeric_rows_compared':len(joined),'max_absolute_difference':float(abs(row.difference)),'maximum_difference_row':{key:str(row[key]) for key in keys},'historical_display':float(row[value+'_historical_display']),'fresh_value':float(row[value+'_fresh']),'available_precision':'Six displayed decimals; exact original persisted assay rows unavailable.'})
 if (folder/'control_cells_coverage.csv').exists():
  output=pd.read_csv(folder/'adjusted_controls.csv');checks=[]
  for binby in ['coverage','plddt']:
   cells=pd.read_csv(folder/f'control_cells_{binby}.csv');columns=['coverage','plddt','log_dms_sd']
   for column in ['am']+columns:cells[column+'_centered']=cells[column]-cells.groupby('assay')[column].transform('mean')
   x=np.column_stack([np.ones(len(cells))]+[cells[column+'_centered'] for column in columns]);y=cells.am_centered.to_numpy()
   beta=np.linalg.lstsq(x,y,rcond=None)[0];target=output[output.binning==binby].set_index('covariate').loc[columns]
   difference=float(np.max(np.abs(beta[1:]-target.beta.to_numpy())));assert difference<1e-12
   checks.append({'binning':binby,'max_absolute_point_difference':difference,'scope':'Exact original centered OLS formula evaluated on current bin rows; no claim of exact old unretained bin-row identity.'})
  result['original_regression_formula_on_current_bins']=checks
 (own/'comparison.json').write_text(json.dumps(result,indent=2)+'\n');reports.append(result)
 print(ident,'old formula/current point checks passed',flush=True)
(OWN/'summary.json').write_text(json.dumps({'analyses':reports,'scope':'No changes to notebooks; original aggregation formulas evaluated on current saved rows. Comparisons to historical outputs are restricted to available displayed precision.','new_cluster_correction_changes_current_point_estimates':False},indent=2)+'\n')
print('Checked',len(reports),'analyses')
