"""Replay the June STATE primary analysis with recovered original inputs.

Original source files remain unchanged. Only path globals and the download
transport are redirected: original Hugging Face downloads resolve to their
recovered, revision-specific local cache. New outputs live in computed/.
"""
from pathlib import Path
import contextlib
import importlib.util
import io
import json
import shutil
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
INITIAL = ROOT / 'original/state_generalizability_20260602_single_controller'
CONTINUED = ROOT / 'original/state_generalizability_continued_20260603'
COMPUTED = ROOT / 'computed'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def modules():
    initial = load_module('original_state_initial', INITIAL/'scripts/run_state_spectra_audit.py')
    base = load_module('state_spectra_loop', CONTINUED/'scripts/state_spectra_loop.py')
    initial.ROOT = COMPUTED/'initial'
    initial.ART = initial.ROOT/'artifacts'
    initial.SPECTRA = initial.ROOT/'spectra_ready_dataset'
    initial.STATE = INITIAL/'external/state'
    initial.CACHE = INITIAL/'hf_cache/hub'
    original_download = initial.hf_hub_download
    download_records = []

    def local_original_download(**kwargs):
        kwargs['cache_dir'] = str(initial.CACHE)
        kwargs['local_files_only'] = True
        path = original_download(**kwargs)
        # Snapshot directory names preserve the exact repository revision.
        parts = Path(path).parts
        revision = parts[parts.index('snapshots')+1] if 'snapshots' in parts else None
        download_records.append(dict(repo=kwargs['repo_id'], path=kwargs['filename'],
                                     revision=revision, local=str(Path(path).relative_to(ROOT))))
        return path

    initial.hf_hub_download = local_original_download
    initial.download_records = download_records
    base.ROOT = COMPUTED/'continued'
    base.PRIOR = INITIAL
    base.ART = base.ROOT/'artifacts'
    base.READY = base.ROOT/'spectra_ready_dataset'
    base.EXT = CONTINUED/'external'
    base.TOML_ROOT = INITIAL/'external/state/state_preprint_toml_files'
    base.TARGET = COMPUTED/'initial/target_model_results.csv'
    for p in [initial.ROOT, initial.ART, initial.SPECTRA, base.ROOT, base.ART, base.READY]:
        p.mkdir(parents=True, exist_ok=True)
    return initial, base


def compare_table(actual, expected_path, keys, columns):
    expected = pd.read_csv(expected_path, low_memory=False)
    actual = actual.copy()
    for key in keys:
        actual[key] = actual[key].astype(str)
        expected[key] = expected[key].astype(str)
    a = actual.set_index(keys).sort_index()
    b = expected.set_index(keys).sort_index()
    assert a.index.equals(b.index), str(expected_path)
    detail = {}
    for col in columns:
        if pd.api.types.is_numeric_dtype(a[col]) and pd.api.types.is_numeric_dtype(b[col]):
            ok = np.isclose(a[col], b[col], rtol=1e-9, atol=1e-10, equal_nan=True)
        else:
            ok = a[col].astype(object).fillna('<NA>').astype(str).eq(b[col].astype(object).fillna('<NA>').astype(str)).to_numpy()
        detail[col] = int((~ok).sum())
    return {'rows':len(actual), 'differences':detail, 'all_match':all(v==0 for v in detail.values())}


def stage_initial(initial, base):
    # Use the original API inventory and cached downloaded CSV/parquet bytes.
    manifest = json.loads((INITIAL/'artifacts/hf_resource_manifest.json').read_text())
    raw, downloads = initial.load_target_results(manifest)
    raw['row_key'] = np.arange(len(raw)).astype(str)
    drugs, genes, cells = initial.load_tahoe_metadata()
    raw = initial.attach_drug_metadata(raw, drugs)
    raw = initial.compute_context_chemical_axis(raw, drugs)
    raw.to_csv(initial.ROOT/'target_model_results.csv', index=False)
    chem = raw[(raw.dataset_family=='Tahoe-100M')&(raw.protocol=='fewshot')&raw.chem_support_level.notna()].copy()
    chem.to_csv(initial.SPECTRA/'tahoe_fewshot_chemical_support_examples.csv', index=False)
    summaries=[]
    trends=[]
    for rep, part in chem.groupby('representation'):
        summary=initial.summarize_axis(part,'chem_support_level','max_tanimoto_to_target_context_train_drug',f'Tahoe fewshot target-context chemical support {rep}')
        summary['representation']=rep
        summaries.append(summary)
        for metric in initial.PRIMARY_METRICS:
            tr=initial.metric_trend(summary,metric);tr['representation']=rep;trends.append(tr)
    pd.concat(summaries,ignore_index=True).to_csv(initial.ART/'spc_tahoe_fewshot_target_context_chemical_support.csv',index=False)
    pd.DataFrame(trends).to_csv(initial.ART/'spc_tahoe_fewshot_target_context_chemical_support_trends.csv',index=False)
    discovery=initial.all_scored_axis_discovery(raw)
    (initial.ART/'all_scored_axis_discovery.json').write_text(json.dumps(discovery,indent=2,default=str))
    dose=initial.dose_axis(raw)
    dose.to_csv(initial.SPECTRA/'exploratory_dose_examples.csv',index=False)
    dose_summaries=[]
    for rep,part in dose.groupby('representation'):
        part=part.copy();part['dose_level']=pd.Categorical(part['dose_level'],ordered=True)
        s=initial.summarize_axis(part,'dose_level','dose',f'Tahoe fewshot dose protocol {rep}');s['representation']=rep;dose_summaries.append(s)
    pd.concat(dose_summaries,ignore_index=True).to_csv(initial.ART/'exploratory_tahoe_dose_protocol_curve.csv',index=False)
    (initial.ART/'download_revisions.json').write_text(json.dumps(initial.download_records,indent=2))
    original = INITIAL/'target_model_results.csv'
    check=compare_table(raw,original,['row_key'],['source_repo','source_path','perturbation','overlap_at_N','de_sig_genes_recall','pearson_delta','max_tanimoto_to_target_context_train_drug','chem_support_level','target_context_train_drug_count'])
    old=pd.read_csv(original,low_memory=False)
    label='nearest_target_context_train_drug'
    differences=raw[label].fillna('').ne(old[label].fillna(''))
    smiles=drugs.set_index('drug').canonical_smiles.to_dict()
    ties=[]
    for index,row in raw.loc[differences].iterrows():
        fp=initial.fingerprint_from_smiles(row.drugmeta_canonical_smiles)
        first=initial.DataStructs.TanimotoSimilarity(fp,initial.fingerprint_from_smiles(smiles[row[label]]))
        second=initial.DataStructs.TanimotoSimilarity(fp,initial.fingerprint_from_smiles(smiles[old.loc[index,label]]))
        ties.append({'row_key':row.row_key,'replay_nearest':row[label],'original_nearest':old.loc[index,label],
                     'replay_pair_similarity':first,'original_pair_similarity':second,'same_similarity':first==second})
    (initial.ROOT/'nearest_reference_ties.json').write_text(json.dumps(ties,indent=2))
    tie_note={'nearest_reference_label_differences':len(ties),'all_are_equal_similarity_ties':all(x['same_similarity'] for x in ties),
              'explanation':'Original code iterates a Python set and chooses the first maximum. Tied nearest-drug labels can differ with hash order; all similarities, level assignments and evaluated outcomes match.'}
    return {'score_files':len(downloads),'score_rows':len(raw),'chemical_rows':len(chem),'drug_metadata_rows':len(drugs),'comparison':check,'tie_note':tie_note}


def stage_replogle(initial, base):
    result=base.run_replogle_reactome_axis(base.load_results())
    fresh=pd.read_csv(base.READY/'replogle_fewshot_reactome_support_examples.csv',low_memory=False)
    columns=['reactome_pathway_count','reactome_max_jaccard_to_train','reactome_pathway_train_support_min','reactome_pathway_train_support_mean','reactome_pathway_train_support_log_mean','hgnc_group_count','hgnc_group_train_support_log_mean','context_train_gene_count','symbol_family_candidate_train_count','reactome_support_level']
    check=compare_table(fresh,CONTINUED/'spectra_ready_dataset/replogle_fewshot_reactome_support_examples.csv',['row_key'],columns)
    return {'comparison':check,'refinement':result['refinement_screen']}


def stage_parse(initial, base):
    result=base.run_parse_family_axis(base.load_results())
    fresh=pd.read_csv(base.READY/'parse_fewshot_ligand_family_support_examples.csv',low_memory=False)
    check=compare_table(fresh,CONTINUED/'spectra_ready_dataset/parse_fewshot_ligand_family_support_examples.csv',['row_key'],['parse_train_ligand_count','parse_family_train_count','parse_family_support_fraction','parse_family_support_level'])
    return {'comparison':check,'freeze':result['freeze']}


def stage_controls(initial, base):
    m=load_module('original_state_controls',CONTINUED/'scripts/state_replogle_controls.py')
    m.ROOT=base.ROOT;m.ART=base.ART;m.READY=base.READY
    m.EXAMPLES=base.READY/'state_replogle_reactome_pathway_log_train_support_v2_examples.csv'
    m.main()
    return {'output':'continued/artifacts/controls_replogle_best_axis_summary.json'}


def stage_zeroshot(initial, base):
    m=load_module('original_state_zeroshot',CONTINUED/'scripts/state_replogle_zeroshot_confirmation.py')
    m.base=base;m.ROOT=base.ROOT;m.ART=base.ART;m.READY=base.READY
    m.main()
    fresh=pd.read_csv(base.READY/'replogle_zeroshot_reactome_support_confirmation_examples.csv',low_memory=False)
    check=compare_table(fresh,CONTINUED/'spectra_ready_dataset/replogle_zeroshot_reactome_support_confirmation_examples.csv',['row_key'],['zeroshot_reactome_support_norm_log_mean','zeroshot_norm_support_level_from_fewshot_freeze'])
    return {'comparison':check}


def stage_ontology(initial, base):
    m=load_module('original_state_multi',CONTINUED/'scripts/state_multi_pathway_support.py')
    m.base=base;m.ROOT=base.ROOT;m.ART=base.ART;m.READY=base.READY;m.EXT=base.EXT
    # Every download function sees the recovered historical file and returns
    # without network access. Refuse network replacement if an input is absent.
    def require_original(url,path,*args,**kwargs):
        assert Path(path).is_file() and Path(path).stat().st_size, str(path)
        return True
    m.download=require_original;m.fetch_text=require_original
    m.main()
    checks={}
    for name in ['reactome','hgnc_gene_group','go_bp','go_mf','go_cc','wikipathways','kegg']:
        for protocol in ['fewshot','zeroshot']:
            namepath=f'multi_pathway_{name}_{protocol}_examples.csv'
            fresh=pd.read_csv(base.READY/namepath,low_memory=False)
            checks[name+'_'+protocol]=compare_table(fresh,CONTINUED/'spectra_ready_dataset'/namepath,['row_key'],['feature_count','support_norm_log_mean','support_level'])
    return {'comparisons':checks}


def stage_history(initial, base):
    result=base.run_all_scored_discovery(base.load_results())
    return {'candidate_screen':result}


DEPENDENCIES={'initial':[], 'replogle':['initial'], 'parse':['initial'], 'controls':['replogle'], 'zeroshot':['replogle'], 'ontology':['replogle'], 'history':['initial']}


def run_stage(name, force=False):
    for dependency in DEPENDENCIES[name]:
        run_stage(dependency)
    marker=COMPUTED/(name+'_verification.json')
    if marker.is_file() and not force:
        return json.loads(marker.read_text())
    initial,base=modules()
    stream=io.StringIO()
    with contextlib.redirect_stdout(stream):
        result=globals()['stage_'+name](initial,base)
    (COMPUTED/(name+'_stdout.txt')).write_text(stream.getvalue())
    marker.write_text(json.dumps(result,indent=2,default=str))
    return result


if __name__=='__main__':
    for stage in (sys.argv[1:] or list(DEPENDENCIES)):
        print(stage,flush=True)
        result=run_stage(stage)
        print(json.dumps(result,indent=2,default=str),flush=True)
