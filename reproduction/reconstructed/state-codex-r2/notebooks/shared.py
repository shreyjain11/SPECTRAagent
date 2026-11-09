"""Presentation/orchestration for reconstructed original Codex r2 investigations."""
from pathlib import Path
from io import BytesIO
import ast,json,subprocess,sys
import numpy as np
import pandas as pd
from IPython.display import Code,Image,JSON,Markdown,display


def run_pipeline(root,stage):
    command=[sys.executable,str(root/'methods/run_pipeline.py'),'--root',str(root),'--stage',stage,'--force']
    print('Calculating the original source workflow for',stage,'; source files are verified before reuse.')
    subprocess.run(command,cwd=root,check=True)
    receipt=read_json(root,f'computed/pipeline_{stage}_receipt.json')
    if not receipt.get('completed') or receipt.get('derived_stage_policy')!='recompute_from_source_inputs':
        raise ValueError('Notebook default requires actual source calculation, not derived-output reuse.')
    display(JSON(receipt))
    return receipt


def read_json(root,relative):
    p=root/relative
    if not p.is_file():raise FileNotFoundError(f'Required stage output missing: {relative}; no historical-output fallback is used.')
    return json.loads(p.read_text())


def read_csv(root,relative):
    p=root/relative
    if not p.is_file():raise FileNotFoundError(f'Required stage output missing: {relative}; no historical-output fallback is used.')
    return pd.read_csv(p)


def source_functions(root,relative,names):
    source=(root/relative).read_text();tree=ast.parse(source)
    nodes={n.name:n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    for name in names:
        node=nodes[name]
        display(Markdown(f'**Executed implementation:** `{relative}::{name}`'))
        display(Code('\n'.join(source.splitlines()[node.lineno-1:node.end_lineno]),language='python'))


def fits(value,path=()):
    rows=[]
    if isinstance(value,dict):
        if 'coefficient' in value:
            rows.append({'fit':' / '.join(path),**{k:v for k,v in value.items() if isinstance(v,(str,int,float,bool)) or k in ['ci95','design_columns']}})
        for k,v in value.items():
            if isinstance(v,(dict,list)):rows.extend(fits(v,(*path,str(k))))
    elif isinstance(value,list):
        for k,v in enumerate(value):rows.extend(fits(v,(*path,str(k))))
    return rows


def show_fits(value):
    table=pd.DataFrame(fits(value))
    if table.empty:raise ValueError('No calculated regression coefficients in supplied output')
    display(table);return table


def show_curve(root,filename):
    p=root/'computed/figures'/filename
    if not p.is_file():raise FileNotFoundError(f'Calculated figure missing: {p}')
    display(Image(filename=str(p)))


def original_rows(root,ids):
    ledger=read_csv(root,'originals/supporting/audit/candidate_axis_ledger.csv')
    selected=ledger.loc[ledger.candidate_id.isin(ids)]
    if set(selected.candidate_id)!=set(ids):raise ValueError('Original ledger IDs missing')
    display(selected[['candidate_id','axis','status','decision_reason','next_action']])
    print('These are attributed original decisions, not new adjudications.')
    return selected


def source_receipts(root,names):
    for name in names:
        receipt=read_json(root,f'computed/{name}_receipt.json')
        if receipt.get('historical_outputs_used_as_calculation_inputs') is not False:
            raise ValueError('Calculation provenance does not exclude historical outcome inputs')
        display(Markdown('**Calculated stage:** '+name))
        display(JSON({k:receipt[k] for k in ['scientific_execution_host','checks','documented_assumptions'] if k in receipt}))


def compare(root,relative):
    values=read_json(root,relative)
    display(pd.DataFrame(values) if isinstance(values,list) else JSON(values))
    print('Original recorded numbers are comparison targets; differences do not select the calculation method.')
