"""Install the current public API and convert the exact original cached weights.

No historical installed source is copied. Public conversion utilities are pinned
and verified. The original folding and backbone checkpoints are separate pinned
inputs; current model-repository defaults are never substituted for either.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

BUNDLE = Path(__file__).resolve().parent
PINS = json.loads((BUNDLE/'CURRENT_IMPLEMENTATION_PINS.json').read_text())


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as src:
        for chunk in iter(lambda:src.read(8*1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()


def model_paths(workspace):
    root = Path(workspace).resolve()/'models'
    return {'fold':root/PINS['fold']['revision'], 'backbone':root/PINS['backbone']['revision'],
            'converted':root/'original-weights-transformers-5.22.2'}


def install_environment(workspace, python=sys.executable):
    """Opt-in isolated environment; does not replace the notebook kernel."""
    env = Path(workspace).resolve()/'environment-current'
    interpreter = env/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
    version = subprocess.check_output([str(python),'-c','import sys;print("%d.%d"%sys.version_info[:2])'],text=True).strip()
    if tuple(map(int,version.split('.'))) < (3,11):raise RuntimeError('Current Transformers requires Python3.11 or later')
    if not interpreter.exists():subprocess.run([str(python),'-m','venv',str(env)],check=True)
    subprocess.run([str(interpreter),'-m','pip','install','-r',str(BUNDLE/'requirements-inference.txt')],check=True)
    return str(interpreter)


def verify_original_sources(workspace):
    paths=model_paths(workspace);records=[]
    for part in ['fold','backbone']:
        expected_weights={x['path'] for x in PINS[part]['files'] if x['path'].endswith('.safetensors')}
        actual_weights={p.name for p in paths[part].glob('*.safetensors')}
        if actual_weights!=expected_weights:
            raise ValueError('Pinned source weight inventory differs: '+str(paths[part]))
        for item in PINS[part]['files']:
            path=paths[part]/item['path']
            if not path.is_file():raise FileNotFoundError('Missing pinned original model source: '+str(path))
            if sha256(path)!=item['sha256']:raise ValueError('Original checkpoint hash mismatch: '+str(path))
            records.append(dict(part=part,path=str(path),sha256=item['sha256'],bytes=path.stat().st_size))
    return records


def download_original_sources(workspace):
    from huggingface_hub import snapshot_download
    paths=model_paths(workspace)
    for part in ['fold','backbone']:
        spec=PINS[part]
        snapshot_download(repo_id=spec['repo'],revision=spec['revision'],local_dir=str(paths[part]),
                          allow_patterns=[x['path'] for x in spec['files']])
    records=verify_original_sources(workspace)
    receipt=Path(workspace).resolve()/'original_model_downloads.json'
    receipt.parent.mkdir(parents=True,exist_ok=True);receipt.write_text(json.dumps(records,indent=2))
    return {k:str(v) for k,v in paths.items()}


def _load_converter(name):
    records=json.loads((BUNDLE/'current_conversion/SOURCE_MANIFEST.json').read_text())
    item=next(x for x in records if x['path']==f'convert_{name}_checkpoint.py')
    path=BUNDLE/'current_conversion'/item['path']
    if sha256(path)!=item['sha256']:raise ValueError('Public conversion utility changed: '+str(path))
    module_name=f'transformers.models.{name}.convert_{name}_checkpoint'
    spec=importlib.util.spec_from_file_location(module_name,path)
    module=importlib.util.module_from_spec(spec);sys.modules[module_name]=module;spec.loader.exec_module(module)
    return module


def convert_original_sources(workspace):
    """Run only inside the current inference environment (CPU conversion)."""
    import transformers
    import torch
    from huggingface_hub import save_torch_state_dict
    from safetensors import safe_open
    if transformers.__version__!=PINS['transformers']:
        raise RuntimeError('Conversion requires transformers=='+PINS['transformers'])
    sources=verify_original_sources(workspace);paths=model_paths(workspace);out=paths['converted']
    original_config=json.loads((paths['fold']/'config.json').read_text())
    config_flags={key:original_config[key] for key in ['disable_msa_features','force_lm_dropout_during_inference','msa_encoder_overwrite','type']}
    config_flags.update({key+'.enabled':original_config[key]['enabled'] for key in ['msa_encoder','lm_encoder','confidence_head','parcae']})
    if out.exists() and any(out.iterdir()):
        # A saved receipt binds this directory to original source bytes, rather
        # than accepting an arbitrary existing native checkpoint.
        return verify_converted_sources(workspace)
    _load_converter('esmc');converter=_load_converter('esmfold2')
    config=converter.build_config(str(paths['fold']),str(paths['backbone']))
    state=converter.merge_state_dict(str(paths['fold']),str(paths['backbone']))
    converter.check_against_model(state,config)
    out.mkdir(parents=True,exist_ok=True);config.save_pretrained(out)
    save_torch_state_dict(state,str(out));converter.save_tokenizer(str(out))
    # Verify every saved value against the deterministic mapping of the exact
    # original tensors. No training, random initialization, or alternate model.
    compared=0
    for shard in sorted(out.glob('*.safetensors')):
        with safe_open(str(shard),framework='pt',device='cpu') as f:
            for key in f.keys():
                actual=f.get_tensor(key)
                if not torch.equal(actual,state[key]):raise ValueError('Converted tensor changed: '+key)
                compared+=1
    if compared!=len(state):raise ValueError('Converted tensor count differs')
    files=[dict(path=p.name,sha256=sha256(p),bytes=p.stat().st_size) for p in sorted(out.iterdir()) if p.is_file()]
    report=dict(status='converted_and_verified',transformers=transformers.__version__,torch=torch.__version__,
                source_revisions={k:PINS[k]['revision'] for k in ['fold','backbone']},original_source_files=sources,
                converter_commit=PINS['converter_commit'],tensor_keys_shapes_checked=True,
                saved_tensor_values_exact=True,tensors=compared,files=files,
                source_config_flags=config_flags,
                dropped_unused_folding_tensors=['confidence_head.s_norm.weight','confidence_head.s_norm.bias','confidence_head.s_inputs_to_single.weight','confidence_head.s_input_to_s.weight'],
                numerical_prediction_equivalence='Not established by weight conversion; see implementation comparison report')
    (out/'CONVERSION_REPORT.json').write_text(json.dumps(report,indent=2))
    return report


def verify_converted_sources(workspace):
    path=model_paths(workspace)['converted'];receipt=path/'CONVERSION_REPORT.json'
    if not receipt.is_file():raise RuntimeError('Run RUN_CONVERT_MODEL=True to build a verified native checkpoint from original weights')
    report=json.loads(receipt.read_text())
    expected={k:PINS[k]['revision'] for k in ['fold','backbone']}
    if report.get('source_revisions')!=expected or not report.get('saved_tensor_values_exact'):
        raise ValueError('Converted checkpoint does not certify the pinned original input tensors')
    expected_weights={item['path'] for item in report['files'] if item['path'].endswith('.safetensors')}
    if {p.name for p in path.glob('*.safetensors')}!=expected_weights:
        raise ValueError('Converted checkpoint weight inventory changed')
    for item in report['files']:
        if sha256(path/item['path'])!=item['sha256']:raise ValueError('Converted checkpoint file changed: '+item['path'])
    return report


def convert_in_environment(workspace,python=sys.executable):
    subprocess.run([str(python),str(Path(__file__).resolve()),'convert','--workspace',str(Path(workspace).resolve())],check=True)
    return verify_converted_sources(workspace)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['convert']);parser.add_argument('--workspace',required=True)
    args=parser.parse_args();print(json.dumps(convert_original_sources(args.workspace),indent=2))
