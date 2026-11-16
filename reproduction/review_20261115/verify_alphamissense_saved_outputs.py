#!/usr/bin/env python3
"""Lightweight independent checks of saved outputs; no data acquisition or inference."""
import ast
import json
from io import StringIO
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score
R=Path(__file__).resolve().parents[1]
B=R/'inline/alphamissense'
checks=[]
def add(entry,check,details): checks.append(dict(entry=entry,check=check,details=details))
def notebook(folder,name): return json.loads((B/folder/name).read_text())
def tables(nb):
    for i,c in enumerate(nb['cells']):
        for o in c.get('outputs',[]):
            if 'text/html' in o.get('data',{}):
                for t in pd.read_html(StringIO(''.join(o['data']['text/html']))): yield i,t
# Independent endpoint arithmetic for each of the twelve Kimi notebooks.
for run in (1,2):
    for axis in range(1,7):
        entry=f'am-kimi-r{run}/test-{axis:02d}'
        ts=list(tables(notebook(f'am-kimi-r{run}',f'axis-{axis}.ipynb')))
        curve=next(t for _,t in ts if {'level','score','AUROC','ci_low'}<=set(t.columns))
        col='delta_AUROC' if run==1 else 'delta_last_minus_first'
        contrast=next(t for _,t in ts if col in t.columns)
        results=[]
        for _,row in contrast.iterrows():
            rows=curve[curve.score==row['score']]
            calculated=float(rows.iloc[0].AUROC-rows.iloc[-1].AUROC) * (1 if run==1 else -1)
            error=abs(calculated-float(row[col]));assert error<=2e-6,(entry,row['score'],error)
            results.append(dict(score=row['score'],calculated_from_rounded_curve=calculated,reported=float(row[col]),absolute_error=error))
        add(entry,'endpoint arithmetic for all saved predictors',results)
        # Kimi r2 prints per-gene mean endpoint AUROCs as well as their contrast.
        for _,t in ts:
            if {'first_mean_AUROC','last_mean_AUROC','mean_delta'}<=set(t.columns):
                errors=(t.last_mean_AUROC-t.first_mean_AUROC-t.mean_delta).abs()
                assert (errors<=2e-6).all()
                add(entry,'paired-gene mean endpoint arithmetic',{'rows':len(t),'maximum_absolute_error':float(errors.max())})
# Recompute five depth correlations per Opus run from the 73 printed assay records.
for run in (1,2):
    entry=f'am-opus-r{run}/test-02';ts=list(tables(notebook(f'am-opus-r{run}','test-02.ipynb')))
    data=next(t for _,t in ts if {'agreement','depth','selection','split','n_variants'}<=set(t.columns))
    summary=next(t for _,t in ts if {'subset','n_assays','rho','p'}<=set(t.columns))
    subsets={'All':data,'Excluding stability':data[data.selection!='Stability'],'Stability only':data[data.selection=='Stability'],'Discovery':data[data.split=='discovery'],'Confirmation':data[data.split=='confirmation']}
    results=[]
    for _,row in summary.iterrows():
        d=subsets[row['subset']];rho,p=spearmanr(d.depth,d.agreement)
        assert len(d)==int(row.n_assays)
        assert abs(rho-float(row.rho))<=2e-6 and abs(p-float(row.p))<=2e-6
        results.append(dict(subset=row['subset'],n=len(d),rho=float(rho),p=float(p)))
    add(entry,'recomputed Spearman correlations from printed per-assay records',results)
# Verify the implemented weighted-AUROC helper against sklearn, including ties and zero weights.
nb=notebook('am-gpt-r1','axis-1.ipynb')
source=next(''.join(c['source']) for c in nb['cells'] if 'def weighted_auc_sorted' in ''.join(c['source']))
f=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='weighted_auc_sorted')
scope={'np':np};exec(compile(ast.Module(body=[f],type_ignores=[]),'saved weighted_auc_sorted','exec'),scope)
rng=np.random.default_rng(20261115);errors=[]
for _ in range(100):
    y=rng.integers(0,2,200);scores=rng.integers(-5,6,200).astype(float);weights=rng.integers(0,5,200).astype(float)
    ours=scope['weighted_auc_sorted'](y,scores,weights);reference=roc_auc_score(y,scores,sample_weight=weights)
    errors.append(abs(ours-reference))
assert max(errors)<1e-12
add('am-gpt-r1/test-01','weighted-AUROC helper against sklearn',{'trials':100,'ties':True,'zero_weights':True,'maximum_absolute_error':max(errors)})
# Verify exact bin-boundary interpretation discussed in Opus r2 coverage note.
levels=pd.cut(pd.Series([0.0,.5,.5000001,.95,.9500001,1.0]),[-.001,.5,.95,1.001],labels=False).tolist()
assert levels==[0,0,1,1,2,2]
add('am-opus-r2/test-03','right-closed coverage-bin boundary check',{'values':[0,.5,.5000001,.95,.9500001,1],'levels':levels})
# Structural check of every saved entry, not proof of scientific validity.
count=0
for p in sorted(B.glob('*/*.ipynb')):
    n=json.loads(p.read_text());count+=1
    assert not any(o.get('output_type')=='error' for c in n['cells'] for o in c.get('outputs',[])),p
assert count==34
payload={'scope':'Independent arithmetic and helper checks against saved notebook outputs. No fresh inference, full notebook execution, original chronology reconstruction, or raw-input download was performed by this script.','notebooks_inspected_for_saved_errors':count,'check_count':len(checks),'checks':checks}
(R/'review_20261115/alphamissense-numerical-checks.json').write_text(json.dumps(payload,indent=2)+'\n')
print(f'{len(checks)} numerical checks; all {count} saved notebooks inspected for error outputs.')
