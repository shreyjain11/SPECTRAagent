# Notebook cell 3
from pathlib import Path
import os, sys
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'original_pipeline.py').is_file())
# True downloads the pinned inputs and executes the original 12,980-image
# CONCH workflow. False is the explicitly labelled historical replay.
RUN_ORIGINAL_WORKFLOW = os.environ.get('SPECTRA_RUN_ORIGINAL_WORKFLOW','0') == '1'
if RUN_ORIGINAL_WORKFLOW and sys.version_info[:2] != (3,11):
    raise RuntimeError('Use the documented Python 3.11 notebook environment for the original workflow; compiled numerical packages must match the model interpreter ABI.')
INFERENCE_PYTHON = Path(os.environ.get('CONCH_INFERENCE_PYTHON', str(ROOT/'.venv-inference/bin/python')))
RUN_DIRECTORY = Path(os.environ.get('CONCH_RUN_DIRECTORY', str(ROOT/'generated/original-workflow')))
ALLOW_CPU_INFERENCE = False  # CUDA was used originally; CPU requires this deliberate opt-in.
print('Selected mode:', 'ORIGINAL WORKFLOW — image acquisition and new scoring' if RUN_ORIGINAL_WORKFLOW else 'HISTORICAL REPLAY — retained target scores')

# Notebook cell 5
from pathlib import Path
import os, sys, subprocess, tempfile, json
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'reconstruct_reference.py').is_file())
sys.path.insert(0,str(ROOT))
from bootstrap_replay import materialize
replay_payload=materialize()
print(f'Verified and materialized {len(replay_payload)} bundled replay tables/manifests; no image download.')
# Isolated, pinned numerical libraries: no changes to the notebook environment.
reference_site=Path(tempfile.gettempdir())/f'conch-reference-numeric-20261108-py{sys.version_info.major}{sys.version_info.minor}'
# A prior recovery cache is reusable only after real compiled imports succeed
# in this interpreter. New caches are specific to the interpreter ABI.
legacy_site=Path(tempfile.gettempdir())/'conch-reference-numeric-20261108'
if not reference_site.exists() and (legacy_site/'sklearn').is_dir():
    probe=subprocess.run([sys.executable,'-c',
        "import numpy,scipy,sklearn,pandas,pyarrow,PIL;assert numpy.__version__=='2.4.6';assert sklearn.__version__=='1.7.2'"],
        env=dict(os.environ,PYTHONPATH=str(legacy_site)),capture_output=True)
    if probe.returncode==0: reference_site=legacy_site
if not (reference_site/'sklearn').is_dir():
    import importlib.metadata, importlib.util
    expected={'numpy':'2.4.6','scipy':'1.16.2','scikit-learn':'1.7.2','pandas':'3.0.3','Pillow':'12.1.1','pyarrow':'17.0.0','requests':'2.32.3'}
    if all(importlib.metadata.version(k)==v for k,v in expected.items()):
        reference_site=Path(importlib.util.find_spec('numpy').origin).parent.parent
if not (reference_site/'sklearn').is_dir():
    subprocess.run([sys.executable,'-m','pip','install','--target',str(reference_site),
                    '-r',str(ROOT/'requirements_reference.txt')],check=True)
reference_env=dict(os.environ,PYTHONPATH=str(reference_site))
reference_path=ROOT/'data/nct_reference_features.reconstructed.csv'
image_archives=list((ROOT/'data/reference_reconstruction').glob('*_images.zip'))
assert reference_path.exists(), 'Portable reference payload did not materialize.'
# Full-mode acquisition and pixel reconstruction run inside original_pipeline.py.
# Historical replay only needs the exact reconstructed matrix, bundled above.
print('Reference acquisition: exact public revision 97765ecb14bf11ce7bb8779a1097d187844a67cb; first 200 matching-label images per original shard.')
print('Recipe: reconstruct_reference.py; numerical environment: requirements_reference.txt.')

# Notebook cell 6
sys.path.insert(0,str(ROOT))
from original_pipeline import verified_results
if RUN_ORIGINAL_WORKFLOW:
    command=[sys.executable,str(ROOT/'original_pipeline.py'),'--run',
             '--run-dir',str(RUN_DIRECTORY),'--inference-python',str(INFERENCE_PYTHON),
             '--numeric-site',str(reference_site)]
    if ALLOW_CPU_INFERENCE: command.append('--allow-cpu')
    # A failed prerequisite or stage raises here. There is no saved-score fallback.
    subprocess.run(command,check=True)
    RESULT_PATHS=verified_results(RUN_DIRECTORY)
    RUN=RUN_DIRECTORY.resolve()
    DATA_MODE='Generated original-workflow results'
    print((RUN/'workflow_receipt.json').read_text())
else:
    RUN=ROOT/'originals/run'
    RESULT_PATHS={phase:ROOT/'data'/f'{phase}.csv' for phase in ['discovery','confirmation','expansion']}
    RESULT_PATHS['summary']=RUN/'artifacts/spc_analysis/spc_summary.json'
    DATA_MODE='Historical retained results'
print(DATA_MODE)
print('Curve inputs:', {name:str(path) for name,path in RESULT_PATHS.items()})

# Notebook cell 7
from pathlib import Path
import json, hashlib, sys, inspect, ast, io
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from IPython.display import display, Code, Markdown
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents]
            if (p/'SOURCE_MANIFEST.json').is_file() and (p/'originals/scripts').is_dir())
ORIGINAL_RUN = ROOT/'originals/run'
sys.path.insert(0, str(ROOT/'originals/scripts'))
import build_crc_candidate_table as feature_source
import freeze_axes as axis_source
import analyze_spc as analysis_source
manifest = json.loads((ROOT/'SOURCE_MANIFEST.json').read_text())
verified_sources=0
for record in manifest:
    # Reacquisition changes ZIP timestamps and may change CSV serialization.
    # Validate regenerated reference inputs by their per-image digests, pixel
    # features and original downstream outputs below, not container bytes.
    if record['path'].startswith('data/reference_reconstruction/') or record['path'].startswith('data/nct_reference_features.'):
        continue
    path = ROOT/record['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], record['path']
    verified_sources+=1
discovery = pd.read_csv(RESULT_PATHS['discovery'])
summary = json.loads(RESULT_PATHS['summary'].read_text())
assert len(discovery) == 7180 and discovery.sample_id.is_unique
print(f'Verified {verified_sources} published source files; loaded {len(discovery):,} discovery rows from {DATA_MODE}. Regenerated reference inputs are checked separately below.')

# Notebook cell 8
commands = json.loads((ROOT/'originals/executed_commands.json').read_text())
selected_commands = [r for r in commands if
    ('curl -L --fail --show-error --retry' in r['command'] and 'CRC_VAL_HE' in r['command'])
    or ('build_crc_candidate_table.py --nct-per-label' in r['command'])
    or ('hf_hub_download' in r['command'] and 'MahmoodLab/conch' in r['command'])]
for row in selected_commands:
    print(f"Original native-session line {row['native_session_line']} — {row['timestamp']}")
    print(row['command'].replace('\\n','\n'))
    print()
print('Original NCT reference selection: first 200 matching-label records in each of these exact nine shards:')
display(pd.DataFrame([{'label': feature_source.LABEL_NAMES[k],
                      'url': feature_source.HF_BASE+v}
                     for k,v in sorted(feature_source.NCT_REFERENCE_SHARDS.items())]))
display(Code(inspect.getsource(feature_source.build_nct_reference_features), language='python'))

# Notebook cell 10
# Full raw-image acquisition is deliberately separate from the offline replay.
image_manifest=json.loads((ROOT/'data/image_samples.json').read_text())
raw_samples_available=all((ROOT/'data/image_samples'/r['image_path']).is_file() for r in image_manifest)
if raw_samples_available:
    historical_discovery=pd.read_csv(ROOT/'data/discovery.csv').set_index('sample_id')
    checks=[]
    for record in image_manifest:
        raw=(ROOT/'data/image_samples'/record['image_path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==record['sha256']
        old=historical_discovery.loc[record['sample_id']]
        assert hashlib.md5(raw).hexdigest()==old.image_md5
        rebuilt=feature_source.image_features(Image.open(io.BytesIO(raw)),raw)
        errors=[]
        for key,value in rebuilt.items():
            if isinstance(value,str): assert str(old[key])==value
            else:
                errors.append(abs(float(old[key])-float(value)))
                assert np.isclose(old[key],value,atol=5e-7,rtol=0)
        checks.append({'sample_id':record['sample_id'],'numeric_features_checked':len(errors),'maximum_absolute_error':max(errors)})
    display(pd.DataFrame(checks))
else:
    print('18-image sample replay not executed: raw sample images are excluded from this portable Git package.')
if RUN_ORIGINAL_WORKFLOW:
    display(json.loads((RUN/'spectra_ready_dataset/dataset_diagnostics.json').read_text()))
    print('The full workflow generated all 7,180 discovery feature rows from acquired pixels and checked original image identities before scoring.')
display(Code(inspect.getsource(feature_source.image_features),language='python'))

# Notebook cell 13
classes = ['ADI','BACK','DEB','LYM','MUC','MUS','NORM','STR','TUM']
for prefix in ['logit_', 'prob_']:
    scores = discovery[[prefix+c for c in classes]].to_numpy()
    assert np.isfinite(scores).all()
    np.testing.assert_array_equal(scores.argmax(1),discovery.pred)
np.testing.assert_array_equal((discovery.pred==discovery.label).astype(int), discovery.correct)
print(DATA_MODE+': all 7,180 labels/correctness values verified against their nine-class scores.')
display(pd.DataFrame([{'model':model, **analysis_source.metrics(discovery.label,discovery[col])}
                     for model,col in [('CONCH','pred'),('Centroid','baseline_centroid_pred'),
                                       ('Logistic','baseline_logistic_pred')]]))

# Notebook cell 14
def plot_axis(frame, axis, level, expected=None, title=None):
    frame=frame.copy();frame.attrs['axis_col']=axis
    model_cols={'CONCH':'pred','Centroid':'baseline_centroid_pred','Logistic':'baseline_logistic_pred'}
    rows=[]
    for model,pred in model_cols.items():
        metrics=analysis_source.metric_by_level(frame,level,pred)
        if expected is not None:
            key={'CONCH':'target_by_level','Centroid':'baseline_centroid_by_level','Logistic':'baseline_logistic_by_level'}[model]
            for new,old in zip(metrics,expected[key]):
                for name in ['level','n','axis_mean','accuracy','balanced_accuracy','macro_f1','weighted_f1']:
                    np.testing.assert_allclose(new[name],old[name],atol=1e-12,rtol=0)
        rows.extend({'model':model,**m} for m in metrics)
    table=pd.DataFrame(rows)
    fig,axs=plt.subplots(1,2,figsize=(10,3.5),layout='constrained')
    for model,g in table.groupby('model',sort=False):
        axs[0].plot(g.level,g.accuracy,marker='o',label=model)
        axs[1].plot(g.level,g.balanced_accuracy,marker='o',label=model)
    for ax,label in zip(axs,['Accuracy','Balanced accuracy']):
        ax.set(xlabel='Level (similarity decreases →)',ylabel=label,ylim=(0,1));ax.legend(fontsize=8)
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle(DATA_MODE+' — '+(title or axis));plt.show()
    return table

def original_functions(filename,names):
    text=(ROOT/'originals/scripts'/filename).read_text()
    lines=text.splitlines()
    tree=ast.parse(text)
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name in names:
            display(Code('\n'.join(lines[node.lineno-1:node.end_lineno]),language='python'))

# Notebook cell 17
ref=pd.read_csv(reference_path)
assert len(ref)==1800 and ref.groupby('label').size().eq(200).all()
import zipfile
identities=json.loads((ROOT/'data/reference_reconstruction/identities.json').read_text())
raw_reference_available=all((ROOT/'data/reference_reconstruction'/name).is_file() for name in set(r['archive'] for r in identities))
if raw_reference_available:
    for archive_name in sorted(set(r['archive'] for r in identities)):
        with zipfile.ZipFile(ROOT/'data/reference_reconstruction'/archive_name) as archive:
            for identity in [r for r in identities if r['archive']==archive_name]:
                assert hashlib.sha256(archive.read(identity['member'])).hexdigest()==identity['encoded_sha256']
    print('Verified encoded bytes for all 1,800 pinned public reference images.')
else:
    print('Raw reference-image byte checks were not executed: image cache is excluded from Git. The matrix and identities are checksum verified; full workflow reacquires the exact images.')
receipts=json.loads((ROOT/'data/reference_reconstruction/download_receipts.json').read_text())
display(pd.DataFrame([{'shard':r['url'].split('/')[-1],'selected_rows':r['rows_selected'],
                      'downloaded_range_bytes':r['total_range_bytes']} for r in receipts]))
replayed=subprocess.run([sys.executable,str(ROOT/'verify_reference.py')],env=reference_env,
                        check=True,capture_output=True,text=True)
reference_checks=json.loads(replayed.stdout)
assert all(r['level_mismatches']==0 for r in reference_checks['axes'].values())
assert all(r['centroid_prediction_mismatches']==r['logistic_prediction_mismatches']==0
           for r in reference_checks['baselines'].values())
display(pd.DataFrame(reference_checks['axes']).T)
display(pd.DataFrame(reference_checks['baselines']).T)
print('All 28,720 discovery axis-level assignments and all 25,960 baseline labels match the historical outputs.')
print('Float32 kNN distances show small platform differences (max 0.000106); all levels match. Tissue/texture distances agree within 1e-15.')
display(Code((ROOT/'verify_reference.py').read_text(),language='python'))

# Notebook cell 19
AXES={'nct_color_texture_proximity': ('axis_nct_color_texture_similarity', 'level_nct_color_texture_proximity'), 'nct_color_proximity': ('axis_nct_color_similarity', 'level_nct_color_proximity'), 'nct_texture_complexity_proximity': ('axis_nct_texture_complexity_similarity', 'level_nct_texture_complexity_proximity'), 'nct_tissue_fraction_proximity': ('axis_nct_tissue_fraction_similarity', 'level_nct_tissue_fraction_proximity')}

# Notebook cell 20
rows=[]
for name,(axis,level) in AXES.items():
    target=plot_axis(discovery,axis,level,summary['axis_summaries'][name],name)
    mix=pd.crosstab(discovery[level],discovery.label_name,normalize='index')
    ax=mix.plot.bar(stacked=True,figsize=(9,3.5),colormap='tab20')
    ax.set(title=name+' — original class proportions',ylabel='Fraction',xlabel='Original level')
    ax.legend(bbox_to_anchor=(1.02,1),loc='upper left',fontsize=8);plt.tight_layout();plt.show()
    adj=pd.DataFrame(analysis_source.class_adjusted_residual_by_level(discovery,level,'pred'))
    adj.insert(0,'axis',name);rows.append(adj)
display(pd.concat(rows,ignore_index=True))

# Notebook cell 23
messages=json.loads((ROOT/'originals/agent_determinations.json').read_text())
for row in messages:
    if row['native_session_line'] in [411,627,632,707,713,719,725,745]:
        display(Markdown(f"**Original session line {row['native_session_line']} ({row['timestamp']})**\n\n"+row['text']))
display(Markdown('**Original historical final report; regenerated curves above are separate.**'))
display(Markdown((ORIGINAL_RUN/'final_report.md').read_text()))
status=json.loads((ROOT/'recovery_status.json').read_text())
print('Original-source items still not located (not new scientific acceptance criteria):')
for item in status['unresolved_originals']: print('-',item)
print('Portable offline replay: raw-image checks are optional; the generated workflow uses acquired pixels and never substitutes archived target scores.')

