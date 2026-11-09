# Notebook cell 3
from pathlib import Path
import json,hashlib,importlib.util,sys,io
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from IPython.display import display,Image
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
root=next((p for p in [Path.cwd(),*Path.cwd().parents] if (p/'ESM_INPUTS.json').is_file()),None)
assert root is not None,'Extract the full ESMFold2 bundle and open this notebook inside it.'
sys.path.insert(0,str(root))
from bootstrap import ensure_assets
ensure_assets(root)
manifest=json.loads((root/'ESM_INPUTS.json').read_text());P=root/'source/esmfold2';A=P/'reconstruction/prior_axes'
def checked(p):
    p=Path(p);k=str(p.relative_to(root));assert hashlib.sha256(p.read_bytes()).hexdigest()==manifest[k]['sha256'],k
    return p
def read(p):return pd.read_csv(checked(p),low_memory=False)
def module(p):
    p=checked(p);sys.path.insert(0,str(p.parent));spec=importlib.util.spec_from_file_location('replay_'+p.stem,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def equal_curve(got,path,keys,columns):
    old=read(path)
    if 'selection' in old:old=old[old.selection=='best_by_ptm']
    a=got.set_index(keys).sort_index();b=old.set_index(keys).sort_index()
    assert a.index.equals(b.index),'Group identities changed'
    for c in columns:np.testing.assert_allclose(a[c],b[c],rtol=1e-9,atol=1e-10,equal_nan=True,err_msg=c)
    print('Matched original group identities and statistics:',path.name)
def plot_rows(df,level,metric='ca_lddt',label='Retained evaluation'):
    # Replay diagnostic intervals: 2,000 resamples of target records, seed 7.
    # These are not new inference or an additional independent cohort.
    rng=np.random.default_rng(7);rows=[]
    for lev,g in df.groupby(level,observed=True):
        v=g[metric].dropna().to_numpy(float)
        if not len(v):continue
        b=np.array([rng.choice(v,len(v),replace=True).mean() for _ in range(2000)])
        rows.append({'level':lev,'n':len(v),'mean':v.mean(),'lo':np.quantile(b,.025),'hi':np.quantile(b,.975)})
    t=pd.DataFrame(rows);display(t)
    fig,ax=plt.subplots(figsize=(7,4),layout='constrained');ax.errorbar(range(len(t)),t['mean'],yerr=np.vstack([t['mean']-t.lo,t.hi-t['mean']]),marker='o',capsize=3)
    ax.set_xticks(range(len(t)),t.level.astype(str));ax.set(xlabel=level,ylabel=metric,title=label);ax.spines[['top','right']].set_visible(False)
    b=io.BytesIO();fig.savefig(b,format='png',dpi=120);plt.close(fig);display(Image(data=b.getvalue()));return t


# Notebook cell 4

# Original files recovered read-only from exxact05; validation is separate from old bundle hashes.
from IPython.display import HTML, Markdown
import html, tempfile
ORIGINAL_MANIFEST=json.loads((root/'REMOTE_FILE_MANIFEST.json').read_text())
ORIGINAL_HASHES={x['relative_destination']:x for x in ORIGINAL_MANIFEST['files']}
R=root/'original_runs'
def original_checked(p):
    p=Path(p);rel=str(p.relative_to(root));assert rel in ORIGINAL_HASHES,rel
    assert hashlib.sha256(p.read_bytes()).hexdigest()==ORIGINAL_HASHES[rel]['sha256'],rel
    return p
def original_read(p):return pd.read_csv(original_checked(p),low_memory=False)
def original_module(p):
    p=original_checked(p);sys.path.insert(0,str(p.parent))
    name='original_'+hashlib.sha256(str(p).encode()).hexdigest()[:12]
    spec=importlib.util.spec_from_file_location(name,p);mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;spec.loader.exec_module(mod);return mod

def original_sources(run_names, notebook_name):
    # Show the actual original acquisition, processing, inference and decision programs, not a replacement recipe.
    coverage=json.loads((root/'CANDIDATE_COVERAGE.json').read_text())
    selected=[x for x in coverage['files'] if notebook_name in x['notebooks']]
    display(pd.DataFrame([{'file':x['relative_destination'],'original_remote_path':x['remote_path'],'bytes':x['bytes'],'sha256':x['sha256']} for x in selected]))
    for item in selected:
        p=original_checked(root/item['relative_destination'])
        if p.suffix in {'.py','.md'} or p.name in {'commands_run.json','axis_ledger.json','spectra_loop_state.json'} or 'manifest' in p.name or 'definitions' in p.name:
            text=p.read_text()
            display(HTML('<details><summary>'+html.escape(item['relative_destination'])+'</summary><pre style="white-space:pre-wrap">'+html.escape(text)+'</pre></details>'))
    print('Original source files verified:',len(selected))

def archive_curve_gallery(df,label):
    level=next((c for c in ['axis_level','stress_rank','level','external_axis_level','charge_level','acidic_window_level','cys_level','viral_disulfide_score','envelope_fusion_score','surface_lowhelical_score','quartile'] if c in df),None)
    metric=next((c for c in ['ca_lddt_mean','target_ca_lddt_mean','ca_lddt'] if c in df),None)
    axis=next((c for c in ['axis_id','axis_name','axis','feature'] if c in df),None)
    if level is None or metric is None:return
    work=df.copy();work['_axis']=work[axis].astype(str) if axis else label
    axes=work['_axis'].unique()
    # Each candidate gets a panel; original source/split/selection curves are kept as separate lines.
    for start in range(0,len(axes),12):
        names=axes[start:start+12];fig,axs=plt.subplots((len(names)+2)//3,3,figsize=(15,3.6*((len(names)+2)//3)),squeeze=False,layout='constrained')
        for ax,name in zip(axs.flat,names):
            sub=work[work['_axis']==name]
            linecols=[c for c in ['subset','source','inference_setting','selection','selection_policy','direction','level_schema','n_levels_requested'] if c in sub]
            grouper=sub.groupby(linecols,dropna=False,sort=False) if linecols else [('original',sub)]
            for key,part in grouper:
                part=part.sort_values(level);ax.plot(part[level],part[metric],marker='.',linewidth=.8,label=str(key))
            ax.set(title=str(name),xlabel=level,ylabel=metric);ax.tick_params(labelsize=7);ax.title.set_fontsize(8)
            if linecols:ax.legend(fontsize=4,loc='best')
        for ax in list(axs.flat)[len(names):]:ax.axis('off')
        buf=io.BytesIO();fig.savefig(buf,format='png',dpi=100);plt.close(fig);display(Image(data=buf.getvalue()))

def original_candidate_tables(notebook_name):
    inventory=json.loads((root/'CANDIDATE_COVERAGE.json').read_text())
    selected=[x for x in inventory['files'] if notebook_name in x['notebooks'] and x.get('screen_or_curve')]
    display(pd.DataFrame([{'source':x['relative_destination'],'screen_rows':x['rows'],'candidate_names':x.get('candidate_count',0)} for x in selected]))
    for item in selected:
        table=original_read(root/item['relative_destination'])
        # All rows, including negatives and discarded directions, remain inspectable in each notebook.
        display(HTML('<details><summary>'+html.escape(item['relative_destination'])+' — '+str(len(table))+' original rows</summary>'+table.to_html(index=False,max_rows=None,max_cols=None)+'</details>'))
        if 'curve' in Path(item['relative_destination']).name:archive_curve_gallery(table,Path(item['relative_destination']).name)
    print('Complete original candidate screens/curves displayed:',len(selected))


# Notebook cell 6
import importlib, subprocess, os
sys.path.insert(0,str(root))
import acquisition, current_implementation, original_workflow
acquisition=importlib.reload(acquisition)
current_implementation=importlib.reload(current_implementation)
original_workflow=importlib.reload(original_workflow)
AXIS_NUMBER = 3
# Set True here, or run execute_notebook.py --original-workflow from ENVIRONMENTS.txt.
RUN_ORIGINAL_WORKFLOW = os.environ.get('SPECTRA_RUN_ORIGINAL_WORKFLOW','0') == '1'
# Shared across all12 notebooks: references, model weights, environment and per-panel results.
REPRODUCTION_DIR = Path(os.environ.get('SPECTRA_ESMFOLD2_WORKSPACE',str(root/'reproduction'/'transformers-5.22.2'))).resolve()
INFERENCE_BACKEND = 'current'
# Optional stage switches allow explicit resume; the master switch activates the entire chain.
RUN_INFERENCE_SETUP = RUN_ORIGINAL_WORKFLOW
RUN_DOWNLOADS = RUN_ORIGINAL_WORKFLOW
RUN_REBUILD_INPUTS = RUN_ORIGINAL_WORKFLOW
RUN_MODEL_DOWNLOAD = RUN_ORIGINAL_WORKFLOW
RUN_CONVERT_MODEL = RUN_ORIGINAL_WORKFLOW
RUN_INFERENCE = RUN_ORIGINAL_WORKFLOW
RUN_RERUN_SUMMARY = RUN_ORIGINAL_WORKFLOW
INFERENCE_PYTHON = str(REPRODUCTION_DIR/'environment-current'/'bin/python')
if RUN_ORIGINAL_WORKFLOW:
    # Install the notebook environment before starting this kernel; do not replace live NumPy/pandas.
    import importlib.metadata as metadata
    required={'numpy':'2.1.2','pandas':'2.3.1'}
    mismatch={k:metadata.version(k) for k,v in required.items() if metadata.version(k)!=v}
    if mismatch:raise RuntimeError('Use the separate notebook environment described in ENVIRONMENTS.txt; incompatible live versions: '+str(mismatch))
if RUN_INFERENCE_SETUP:
    INFERENCE_PYTHON=current_implementation.install_environment(REPRODUCTION_DIR)
plan=acquisition.download_plan(AXIS_NUMBER,REPRODUCTION_DIR)
print('Original panels:',acquisition.panels_for(AXIS_NUMBER))
print('Planned exact source files:',len(plan),'| full workflow enabled:',RUN_ORIGINAL_WORKFLOW)
print('Shared workspace:',REPRODUCTION_DIR)
print('Current package:',current_implementation.PINS['transformers'],'| Torch:',current_implementation.PINS['torch'])
display(pd.DataFrame(plan)[['kind','url','destination']].head(12))
assert all(item.get('sha256') or item.get('git_blob_sha1') for item in plan)


# Notebook cell 7
# Downloaded reference coordinates feed the original accuracy evaluator.
# Recomputed features are materialized in panels/<panel>/features.csv and bound by a hash receipt.
if RUN_DOWNLOADS:
    receipts=acquisition.fetch_references(AXIS_NUMBER,REPRODUCTION_DIR)
    print('Exact source files verified:',len(receipts))
else:
    print('Downloads off; archived analysis replay follows. Enable RUN_ORIGINAL_WORKFLOW for the full chain.')
if RUN_REBUILD_INPUTS:
    rebuilt=acquisition.reconstruct_features(AXIS_NUMBER,REPRODUCTION_DIR)
    display(pd.DataFrame(rebuilt['panels']).T)
else:
    print('Fresh feature reconstruction is off. Frozen cohort IDs and fitted split memberships are preserved when rebuilding.')


# Notebook cell 8
# Model inference is a separate process in environment-current; no old private source is required.
if RUN_MODEL_DOWNLOAD:
    model_directories=acquisition.download_model(REPRODUCTION_DIR,backend=INFERENCE_BACKEND)
    print('Pinned original sources:',model_directories)
if RUN_CONVERT_MODEL:
    conversion=current_implementation.convert_in_environment(REPRODUCTION_DIR,python=INFERENCE_PYTHON)
    print('This conversion run:',conversion['tensors'],'tensors; saved values exact:',conversion['saved_tensor_values_exact'])
if RUN_INFERENCE:
    results=acquisition.run_inference(AXIS_NUMBER,REPRODUCTION_DIR,python=INFERENCE_PYTHON,backend=INFERENCE_BACKEND)
    display(pd.DataFrame(results).T)
if RUN_RERUN_SUMMARY:
    rerun=acquisition.summarize_rerun(AXIS_NUMBER,REPRODUCTION_DIR)
    print('Axis-specific original analyses:',rerun['status'])
    display(pd.DataFrame([{'artifact':k,'path':v} for k,v in rerun['artifacts'].items()]))
    for name,path in rerun['artifacts'].items():
        if name.endswith('.csv') and any(term in name for term in ['curve','screen','effects','summary','candidate']):
            table=pd.read_csv(path)
            display(table)
            archive_curve_gallery(table,'New evaluations: '+name)
if not any([RUN_MODEL_DOWNLOAD,RUN_CONVERT_MODEL,RUN_INFERENCE,RUN_RERUN_SUMMARY]):
    print('Fresh model stages off. Below: original archived measurements, curves and agent decisions.')
comparison=json.loads((root/'IMPLEMENTATION_COMPARISON.json').read_text())
display(comparison)


# Notebook cell 10
original_sources(['esmfold2_beyond_evolutionary_support_final_run', 'esmfold2_external_flexible_axis_expanded_20260601T170049Z'], 'notebooks/test-03.ipynb')


# Notebook cell 11

# Exact 141-target percentile reference and original freeze program.
B=R/'esmfold2_beyond_evolutionary_support_final_run'
feature_builder=original_module(B/'scripts/build_nonerror_features.py')
freeze=original_module(B/'scripts/freeze_followup_axes.py')
reference=original_read(B/'spectra_ready_dataset/prospective_features.csv')
frozen=original_read(B/'spectra_ready_dataset/prospective_features.followup.csv')
assert len(reference)==len(frozen)==141
components=['proline_fraction','chou_beta_minus_helix','chou_turn_minus_helix']
recalculated=pd.DataFrame(reference.sequence.map(feature_builder.sequence_features).tolist())
for col in components:np.testing.assert_allclose(recalculated[col],reference[col],atol=1e-12)
reference['flexible_nonhelical_composite_rank']=freeze.rank_mean(reference,components)
freeze.add_quantile_levels(reference,'flexible_nonhelical_composite_rank',7)
np.testing.assert_allclose(reference.flexible_nonhelical_composite_rank,frozen.flexible_nonhelical_composite_rank,atol=1e-12)
levelcol='axis_flexible_nonhelical_composite_rank_q7_level'
boundary_diff=reference[levelcol].ne(frozen[levelcol])
print('Historical frozen levels matching local qcut replay:',int((~boundary_diff).sum()),'of',len(reference))
if boundary_diff.any():
    display(reference.loc[boundary_diff,['target_id','flexible_nonhelical_composite_rank',levelcol]].assign(original_frozen_level=frozen.loc[boundary_diff,levelcol]))
    print('One exact quantile-boundary assignment differs with this local pandas/NumPy environment. Original frozen labels remain authoritative for the original discovery curve below.')
# External ranks use <= empirical CDF, not the average-tie ranks above. Preserve both original rules.
external_builder=original_module(B/'external_rcsb_same_bucket_expansion_20260531/scripts/build_external_rcsb_bucket_panel.py')
external_pool=original_read(B/'external_rcsb_same_bucket_expansion_20260531/rcsb_external_candidate_pool.csv')
for col in components:
    got=external_pool[col].map(lambda value:external_builder.empirical_pct(frozen[col],value))
    # CSV decimal round-trips can change <= at an exact tie. Recompute the original feature value from sequence.
    raw_values=external_pool.sequence.map(lambda seq:feature_builder.sequence_features(seq)[col])
    got=raw_values.map(lambda value:external_builder.empirical_pct(frozen[col],value))
    delta=got-external_pool[col+'_prior_pct']
    print(col,'external empirical-percentile maximum absolute difference:',float(delta.abs().max()),'matching:',int(np.isclose(got,external_pool[col+'_prior_pct'],atol=1e-12).sum()),'/',len(got))
print('Original 141-row reference, exact freeze/external-percentile programs and 613-row pool recovered. Local numerical boundary behavior is reported above; archived levels and original external ranks are preserved below.')


# Notebook cell 12
D=A/'03_external_flexible';m=module(D/'scripts/summarize_expanded_external_spc.py');g=module(P/'scripts/global_hypothesis_audit.py')
f=read(D/'spectra_ready_dataset/candidate_features.csv');r=read(D/'target_model_results.scaled_samples.csv')
assert f.target_id.is_unique
x=g.add_features(f.assign(sequence_clean=f.sequence.str.upper()))
for a,b in [('proline_fraction_calc','proline_fraction'),('chou_beta_minus_helix_calc','chou_beta_minus_helix'),('chou_turn_minus_helix_calc','chou_turn_minus_helix')]:
    np.testing.assert_allclose(x[a],f[b],atol=1e-10)
rank=f[['proline_fraction_prior_pct','chou_beta_minus_helix_prior_pct','chou_turn_minus_helix_prior_pct']].mean(axis=1)
np.testing.assert_allclose(rank,f.flexible_nonhelical_composite_rank,atol=1e-12)
selected=m.best_by(r,'ptm');d=f.merge(selected,on='target_id',validate='one_to_one',suffixes=('','_metric'));d=d[(d.status=='ok')&d.ca_lddt.notna()]
print('Exact confirmation targets:',len(d),'prediction samples:',len(r));display(d[['target_id','sample_index','external_axis_level','ca_lddt']].head())

# Notebook cell 13
curve,effect=m.summarize('best_by_ptm',selected,f)
equal_curve(curve,D/'expanded_external_spc_by_level.csv',['external_axis_level'],['n','ca_lddt_mean','rank_mean'])
plot_rows(d,'external_axis_level',label='Original external confirmation')
print(json.dumps(effect,indent=2))
for policy,col in [('best_by_plddt','plddt_mean'),('oracle_best_ca_lddt','ca_lddt')]:
    c,e=m.summarize(policy,m.best_by(r,col),f);print(policy,json.dumps(e))

# Notebook cell 14
discovery=read(A/'02_flexible_nonhelical/primary_axis_membership.csv')
assert discovery.target_id.is_unique and len(discovery)==138
level='axis_flexible_nonhelical_composite_rank_q7_level'
top=discovery[discovery[level]==6];rest=discovery[discovery[level]!=6]
print('Original discovery highest-minus-rest:',top.ca_lddt.mean()-rest.ca_lddt.mean())
print('Discovery contrast bootstrap:',m.bootstrap_diff(top.ca_lddt.to_numpy(),rest.ca_lddt.to_numpy()))
plot_rows(discovery,level,label='Original CAMEO discovery')
print('Confirmation-minus-discovery is not a paired experiment: these are separate cohorts.')

# Notebook cell 18
original_candidate_tables('notebooks/test-03.ipynb')

