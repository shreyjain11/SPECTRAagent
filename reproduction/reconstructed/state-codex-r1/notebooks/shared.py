"""Notebook presentation and orchestration; scientific methods live in ../methods.

Historical tables are read only by historical_comparison/decision helpers.
No retained aggregate enters feature construction, scoring, fitting or plotting.
"""
from pathlib import Path
import ast
import json
from io import BytesIO
import os
import subprocess
import sys

import numpy as np
import pandas as pd
from IPython.display import Code, Image, JSON, Markdown, display


def root_path():
    candidates = [Path(os.environ['STATE_RECONSTRUCTION_ROOT'])] if os.environ.get('STATE_RECONSTRUCTION_ROOT') else []
    candidates += [Path.cwd(), *Path.cwd().parents, Path(__file__).resolve().parent.parent]
    return next(p.resolve() for p in candidates if (p/'methods/sources.json').is_file())


def source_functions(root, relative_path, names):
    """Expose the actual calculation code invoked by the shared pipeline."""
    path = root / relative_path
    source = path.read_text()
    tree = ast.parse(source)
    nodes = {n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    for name in names:
        if name not in nodes:
            raise KeyError(f'{name} is not defined in {relative_path}')
        display(Markdown(f'**Executed helper:** `{relative_path}::{name}`'))
        display(Code('\n'.join(source.splitlines()[nodes[name].lineno-1:nodes[name].end_lineno]), language='python'))


def run_pipeline(root):
    """Default Run All recalculates derived features, errors and analyses."""
    command = [sys.executable, str(root/'methods/run_pipeline.py'), '--root', str(root), '--stage', 'all']
    print('Recalculating source → features → released-score metrics → analysis. Existing source downloads are checksum verified before reuse.')
    subprocess.run(command, cwd=root, check=True)
    receipt=json.loads((root/'computed/pipeline_all_receipt.json').read_text())
    if not receipt.get('completed') or receipt.get('derived_stage_policy')!='recompute_from_source_inputs':
        raise ValueError('Default notebook requires completed source recalculation, not derived-output reuse.')
    display(JSON(receipt))
    print('The shared pipeline completed source recalculation. Tables below are newly computed outputs.')


def read_csv(root, relative):
    path = root / relative
    if not path.is_file():
        raise FileNotFoundError(f'Required computed output is absent: {relative}. Run the pipeline cell above; archived results are never substituted.')
    return pd.read_csv(path)


def read_json(root, relative):
    path = root / relative
    if not path.is_file():
        raise FileNotFoundError(f'Required computation receipt/result is absent: {relative}')
    return json.loads(path.read_text())


def show_receipts(root):
    rows = []
    for path in sorted((root/'computed').rglob('*receipt*.json')):
        value = json.loads(path.read_text())
        rows.append({'receipt':str(path.relative_to(root)), 'bytes':path.stat().st_size,
                     'top_level_fields':', '.join(value) if isinstance(value,dict) else f'{len(value)} records'})
    if not rows:
        raise FileNotFoundError('Pipeline produced no computation receipt.')
    display(pd.DataFrame(rows))
    print('Receipts bind source identities, calculation code and computed outputs. This notebook default requests actual recalculation; optional CLI reuse must be requested explicitly.')


def fit_table(value, prefix=()):
    """Flatten fit result dictionaries for display, without recalculating fits."""
    rows = []
    if isinstance(value,dict):
        if 'estimate' in value:
            row={'analysis':' / '.join(prefix)}
            for key,item in value.items():
                if item is None or isinstance(item,(str,int,float,bool)):
                    row[key]=item
                elif key in {'bootstrap_ci95','ci95','controls'}:
                    row[key]=str(item)
            rows.append(row)
        for key,item in value.items():
            if isinstance(item,(dict,list)):
                rows.extend(fit_table(item,(*prefix,str(key))))
    elif isinstance(value,list):
        for i,item in enumerate(value): rows.extend(fit_table(item,(*prefix,str(i))))
    return rows


def show_fits(value, contains=None):
    table=pd.DataFrame(fit_table(value))
    if table.empty:
        raise ValueError('No calculated regression estimates found in analysis output.')
    if contains:
        table=table[table.analysis.str.contains(contains,case=False,regex=False)]
        if table.empty: raise ValueError(f'No calculated fits matched {contains!r}')
    display(table)
    return table


def show_curve(root, axis):
    path=root/'computed/analysis'/axis/'spc.png'
    if not path.is_file(): raise FileNotFoundError(f'Computed curve absent: {path}')
    display(Image(filename=str(path)))


def show_figure(figure):
    """Embed a PNG even when the execution kernel uses a non-inline backend."""
    data=BytesIO()
    figure.savefig(data,format='png',dpi=140,bbox_inches='tight')
    display(Image(data=data.getvalue()))


def show_conditions(conditions):
    required=['target','cell_line','compound','partition','dose','axis_value','state_lfc_rmse','identity_lfc_rmse','n_de','n_cells']
    absent=set(required)-set(conditions)
    if absent: raise ValueError(f'Computed condition table lacks {sorted(absent)}')
    display(conditions[required].head(10))
    counts=conditions.groupby('partition',observed=True).agg(rows=('target','size'),targets=('target','nunique'),compounds=('compound','nunique'),contexts=('cell_line','nunique'))
    display(counts)
    assert conditions.groupby('compound').partition.nunique().max()==1
    assert not conditions[['state_lfc_rmse','identity_lfc_rmse','axis_value','n_cells']].isna().any().any()
    print('Every displayed observation is a real context × released drug-dose target, not an expanded aggregate mean.')


def historical_paths(root):
    base=root/'recovery/original_handoff'
    return base/'REPORT.md', base/'supporting/results/final_closure_verdict.json'


def historical_comparison(root, axis=None):
    table=read_csv(root,'computed/analysis/historical_comparison.csv')
    if axis is not None:
        # Match the report's explicit analysis label, not arbitrary numerical values.
        candidates=[c for c in ['axis','analysis','candidate','run'] if c in table]
        if candidates:
            mask=pd.Series(False,index=table.index)
            for col in candidates: mask |= table[col].astype(str).str.contains(axis,case=False,regex=False)
            if mask.any(): table=table.loc[mask]
    display(table)
    print('Historical values are validation targets only. Differences are reported rather than used to tune inputs or calculations.')
    return table


def original_decision(root, key, explanation):
    _,path=historical_paths(root)
    decision=json.loads(path.read_text())
    display(Markdown(f"**Original decision:** `{decision['primary_candidates'][key]}`\n\n{explanation}"))
    print('Historical overall disposition:',decision['verdict'])
    print('This records the original agent determination; it does not create a new scientific certification.')
