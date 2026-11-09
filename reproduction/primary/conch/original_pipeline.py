"""Execute the recovered CONCH workflow; no archived target-score fallback.

Use --plan for a read-only plan. Actual execution is deliberately opt-in via
--run; notebooks call that only when RUN_ORIGINAL_WORKFLOW is True.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
DATA_REVISION = '97765ecb14bf11ce7bb8779a1097d187844a67cb'
SOURCE_REVISION = '141cc09c7d4ff33d8eda562bd75169b457f71a62'
CHECKPOINT_REVISION = 'f9ca9f877171a28ade80228fb195ac5d79003357'
PROMPT = 'prompts/crc100k_prompts_all_per_class.json'
CRC_SHARDS = [
    'data/CRC_VAL_HE_7K-00000-of-00003-cce1097526b69125.parquet',
    'data/CRC_VAL_HE_7K-00001-of-00003-fbb5de8b1164f4ea.parquet',
    'data/CRC_VAL_HE_7K-00002-of-00003-2009e87e0c48fccf.parquet',
]
TUM_SHARDS = [
    'data/NCT_CRC_HE_100K_NONORM-00017-of-00031-185be2828f60b3a7.parquet',
    'data/NCT_CRC_HE_100K_NONORM-00018-of-00031-20db16691204a5c6.parquet',
    'data/NCT_CRC_HE_100K_NONORM-00019-of-00031-9be5fae292c61245.parquet',
    'data/NCT_CRC_HE_100K_NONORM-00020-of-00031-cf3901477d5683dd.parquet',
]
STAGES = [
    'source', 'images', 'checkpoint', 'reference', 'discovery_features',
    'freeze_discovery', 'score_discovery', 'analyze_discovery',
    'freeze_confirmation', 'score_confirmation', 'analyze_confirmation',
    'freeze_expansion', 'score_expansion', 'analyze_expansion', 'report_expansion',
]


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def dump(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2))
    temporary.replace(path)


def result_paths(run):
    run = Path(run)
    return {
        'discovery': run / 'artifacts/spc_analysis/scored_table_with_axes_and_baselines.csv',
        'summary': run / 'artifacts/spc_analysis/spc_summary.json',
        'confirmation': run / 'artifacts/tum_confirmation/scored_tum_confirmation_with_baselines.csv',
        'expansion': run / 'artifacts/tum_expansion/scored_tum_confirmation_with_baselines.csv',
    }


def verified_results(run):
    """Reject incomplete, altered, or archive-relabelled rerun results."""
    run = Path(run).resolve()
    receipt = json.loads((run / 'workflow_receipt.json').read_text())
    assert receipt.get('completed') and receipt.get('mode') == 'raw_images_to_CONCH_predictions'
    assert receipt['stages'] == STAGES
    for name in ['score_discovery', 'score_confirmation', 'score_expansion']:
        stage = json.loads((run / 'receipts' / (name + '.json')).read_text())
        assert stage.get('executed_original_model_scoring') is True, name
        for path, expected in stage['outputs'].items():
            assert digest(path) == expected, path
    for path, expected in receipt['result_hashes'].items():
        assert digest(path) == expected, path
    return result_paths(run)


def preflight(python, allow_cpu):
    if not Path(python).is_file():
        raise RuntimeError('CONCH inference environment missing. Run Python 3.11 setup_inference.py first, '
                           'or set CONCH_INFERENCE_PYTHON to its bin/python. No target scores were substituted.')
    script = """import sys,json,importlib.metadata as m
import torch,torchvision,timm,transformers,datasets,pyarrow,PIL,ftfy,h5py
from pathlib import Path
expected=dict(line.strip().split('==') for line in Path(sys.argv[1]).read_text().splitlines()
              if line.strip() and not line.lstrip().startswith('#'))
assert sys.version_info[:2]==(3,11), 'Use Python 3.11'
for k,v in expected.items(): assert m.version(k).split('+')[0]==v, (k,m.version(k),v)
print(json.dumps({'python':sys.version,'cuda_available':torch.cuda.is_available(),
 'cuda_version':torch.version.cuda,'packages':{k:m.version(k) for k in expected},
 'device':torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'}))
"""
    environment = dict(os.environ)
    environment.pop('PYTHONPATH', None)
    result = subprocess.run([str(python), '-c', script, str(ROOT / 'requirements_inference.txt')], check=True, text=True,
                            capture_output=True, env=environment)
    details = json.loads(result.stdout)
    if not details['cuda_available'] and not allow_cpu:
        raise RuntimeError('Original scoring used CUDA. Select a visible CUDA device, or explicitly set '
                           'ALLOW_CPU_INFERENCE=True / --allow-cpu for the slower CPU route.')
    return details


class Pipeline:
    def __init__(self, run, inference_python, numeric_site, allow_cpu=False):
        self.run = Path(run).resolve()
        if self.run == ROOT or ROOT / 'originals' in [self.run, *self.run.parents]:
            raise ValueError('Use a separate generated run folder, never originals.')
        self.python = str(Path(inference_python).resolve())
        self.numeric_site = Path(numeric_site).resolve()
        self.environment = preflight(self.python, allow_cpu)
        self.base_env = dict(os.environ)
        self.base_env.pop('PYTHONPATH', None)
        self.numeric_env = dict(self.base_env, PYTHONPATH=str(self.numeric_site))
        numeric_check = """import json,importlib.metadata as m
import numpy,scipy,sklearn,pandas,PIL,pyarrow,requests
from sklearn.linear_model import LogisticRegression
LogisticRegression(multi_class='auto',max_iter=1000,C=1.0,solver='lbfgs',random_state=0)
expected={'numpy':'2.4.6','scipy':'1.16.2','scikit-learn':'1.7.2','pandas':'3.0.3','Pillow':'12.1.1','pyarrow':'17.0.0','requests':'2.32.3'}
actual={k:m.version(k) for k in expected}
assert actual==expected, ('Reinstall requirements_reference.txt into the numeric-site',actual)
print(json.dumps(actual))
"""
        checked = subprocess.run([self.python, '-c', numeric_check], env=self.numeric_env,
                                 check=True, text=True, capture_output=True)
        self.environment['numeric_packages'] = json.loads(checked.stdout)
        self.source = self.run / 'source/CONCH'
        self.data = self.run / 'data_cache'
        self.checkpoint = self.run / 'model_cache/pytorch_model.bin'
        for path in ['receipts', 'logs', 'spectra_ready_dataset', 'artifacts/tum_confirmation', 'artifacts/tum_expansion']:
            (self.run / path).mkdir(parents=True, exist_ok=True)
        files = [*sorted((ROOT / 'originals/scripts').glob('*.py')),
                 ROOT / 'original_pipeline.py', ROOT / 'run_original_stage.py',
                 ROOT / 'acquire_original_inputs.py', ROOT / 'requirements_inference.txt',
                 ROOT / 'requirements_reference.txt']
        self.fingerprint = hashlib.sha256(json.dumps({
            'files': {str(p.relative_to(ROOT)): digest(p) for p in files},
            'pins': [DATA_REVISION, SOURCE_REVISION, CHECKPOINT_REVISION],
            'environment': self.environment,
        }, sort_keys=True).encode()).hexdigest()
        self.completed = []

    def command(self, command, name, numeric=False):
        with (self.run / 'logs' / (name + '.log')).open('w') as log:
            log.write(json.dumps([str(v) for v in command]) + '\n'); log.flush()
            result = subprocess.run([str(v) for v in command], cwd=self.run,
                                    env=self.numeric_env if numeric else self.base_env,
                                    stdout=log, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError(f'{name} failed; see {self.run / "logs" / (name + ".log")}. '
                               'The workflow stopped; archived scores are never used as a substitute.')

    def stage(self, name, outputs, action, inputs=()):
        outputs = [Path(p).resolve() for p in outputs]
        key = hashlib.sha256(json.dumps({'pipeline': self.fingerprint,
                'inputs': {str(p): digest(p) for p in inputs}}, sort_keys=True).encode()).hexdigest()
        receipt_path = self.run / 'receipts' / (name + '.json')
        old = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
        if old.get('fingerprint') == key and all(p.exists() and old.get('outputs', {}).get(str(p)) == digest(p) for p in outputs):
            print('Reusing verified stage:', name, flush=True)
        else:
            print('Running original workflow stage:', name, flush=True)
            action()
            receipt = {'stage': name, 'fingerprint': key, 'completed_utc': time.time(),
                       'outputs': {str(p): digest(p) for p in outputs},
                       'executed_original_model_scoring': name.startswith('score_')}
            dump(receipt_path, receipt)
        self.completed.append(name)

    def original(self, name, module, args=(), numeric=True):
        self.command([self.python, ROOT / 'run_original_stage.py', '--module', module,
                      '--data-root', self.data, '--', *args], name, numeric)

    def freeze(self, name, module, outputs, args, inputs):
        # Original builders update one shared ledger. Keep each stage's frozen
        # snapshot immutable so later updates do not invalidate resume hashes.
        snapshot = self.run / 'receipts' / (name + '_axis_ledger.json')
        def action():
            self.original(name, module, args)
            shutil.copyfile(self.run / 'axis_ledger.json', snapshot)
        self.stage(name, [*outputs, snapshot], action, inputs)
        shutil.copyfile(snapshot, self.run / 'axis_ledger.json')

    def source_setup(self):
        if not (self.source / '.git').exists():
            self.source.mkdir(parents=True, exist_ok=True)
            self.command(['git', 'init', self.source], 'source_init')
        self.command(['git', '-C', self.source, 'fetch', '--depth', '1',
                      'https://github.com/mahmoodlab/CONCH.git', SOURCE_REVISION], 'source_fetch')
        self.command(['git', '-C', self.source, 'checkout', '--detach', SOURCE_REVISION], 'source_checkout')
        commit = subprocess.check_output(['git', '-C', str(self.source), 'rev-parse', 'HEAD'], text=True).strip()
        assert commit == SOURCE_REVISION
        dirty = subprocess.check_output(['git', '-C', str(self.source), 'status', '--porcelain', '--untracked-files=no'], text=True)
        assert not dirty, 'Source checkout contains edits; use a clean run directory.'
        prompts = json.loads((self.source / PROMPT).read_text())['0']
        classes = ['ADI', 'BACK', 'DEB', 'LYM', 'MUC', 'MUS', 'NORM', 'STR', 'TUM']
        assert set(classes) == set(prompts['classnames']) and prompts['templates']
        files = {str(p.relative_to(self.source)): digest(p) for p in self.source.rglob('*')
                 if p.is_file() and '.git' not in p.parts and '__pycache__' not in p.parts}
        dump(self.run / 'source_receipt.json', {'commit': commit, 'files': files,
             'prompt_path': PROMPT, 'prompt_sha256': digest(self.source / PROMPT),
             'ordered_classes': classes, 'classnames': [prompts['classnames'][c] for c in classes],
             'templates': prompts['templates']})
        self.command([self.python, '-c',
            "import sys;sys.path.insert(0,sys.argv[1]);from conch.open_clip_custom import create_model_from_pretrained;from conch.downstream.zeroshot_path import zero_shot_classifier;print('Original CONCH imports succeeded')",
            self.source], 'source_imports')

    def acquire(self, kind):
        dataset = kind == 'images'
        request = {'repo_id': '1aurent/NCT-CRC-HE' if dataset else 'MahmoodLab/conch',
                   'repo_type': 'dataset' if dataset else 'model',
                   'revision': DATA_REVISION if dataset else CHECKPOINT_REVISION,
                   'filenames': CRC_SHARDS + TUM_SHARDS if dataset else ['pytorch_model.bin']}
        request_path = self.run / (kind + '_request.json')
        dump(request_path, request)
        self.command([self.python, ROOT / 'acquire_original_inputs.py', '--request', request_path,
                      '--destination', self.data if dataset else self.checkpoint.parent,
                      '--receipt', self.run / (kind + '_receipt.json')], kind)

    def execute(self):
        dump(self.run / 'workflow_receipt.json', {'completed': False, 'mode': 'raw_images_to_CONCH_predictions'})
        self.stage('source', [self.run / 'source_receipt.json', self.source / PROMPT], self.source_setup)
        # Check every tracked source byte on resume, including model/tokenizer code.
        for file, value in json.loads((self.run / 'source_receipt.json').read_text())['files'].items():
            assert digest(self.source / file) == value, file
        self.stage('images', [self.run / 'images_receipt.json', *[self.data / f for f in CRC_SHARDS + TUM_SHARDS]], lambda: self.acquire('images'))
        self.stage('checkpoint', [self.run / 'checkpoint_receipt.json', self.checkpoint], lambda: self.acquire('checkpoint'))
        reference = ROOT / 'data/nct_reference_features.reconstructed.csv'
        def reference_stage():
            self.command([self.python, ROOT / 'reconstruct_reference.py'], 'reference', numeric=True)
        self.stage('reference', [reference], reference_stage,
                   [ROOT / 'reconstruct_reference.py', ROOT / 'replay_reference_pixels.py'])
        candidate = self.run / 'spectra_ready_dataset/candidate_features.csv'
        ref_copy = self.run / 'spectra_ready_dataset/nct_reference_features.csv'
        self.stage('discovery_features', [candidate, ref_copy],
            lambda: self.command([self.python, ROOT / 'run_original_stage.py', '--module', 'build_features',
                '--data-root', self.data, '--reference', reference, '--output', candidate.parent], 'discovery_features', True),
            [reference, self.run / 'images_receipt.json'])
        frozen = candidate.parent / 'spectra_ready_table.csv'
        self.freeze('freeze_discovery', 'freeze_axes', [frozen], [], [candidate])
        model_args = ['--conch-source', self.source, '--checkpoint', self.checkpoint,
                      '--prompt-json', self.source / PROMPT, '--batch-size', '128']
        model_inputs = [self.run / 'source_receipt.json', self.run / 'checkpoint_receipt.json', self.run / 'images_receipt.json']
        scores = self.run / 'target_model_results.csv'
        self.stage('score_discovery', [scores, self.run / 'artifacts/target_model_summary.json'],
            lambda: self.original('score_discovery', 'score_conch_crc_val',
                [*model_args, '--parquet-dir', self.data / 'data'], False), [frozen, *model_inputs])
        results = result_paths(self.run)
        self.stage('analyze_discovery', [results['discovery'], results['summary']],
            lambda: self.original('analyze_discovery', 'analyze_spc'), [candidate, frozen, scores])
        previous = None
        for phase, count in [('confirmation', 600), ('expansion', 1000)]:
            panel = candidate.parent / ('tum_' + phase + '_panel.csv')
            folder = self.run / ('artifacts/tum_' + phase)
            panel_args = ['--per-shard', str(count), '--levels', '6' if phase == 'confirmation' else '10']
            inputs = [ref_copy, self.run / 'images_receipt.json'] + ([previous] if previous else [])
            panel_outputs = [panel] + ([folder / 'panel_diagnostics.json'] if phase == 'expansion' else [])
            self.freeze('freeze_' + phase, 'build_tum_' + phase + '_panel', panel_outputs, panel_args, inputs)
            scores = folder / ('target_model_results_tum_' + phase + '.csv')
            score_args = [*model_args, '--panel', panel, '--out', scores, '--summary', folder / 'summary.json']
            scorer = 'score_tum_confirmation' if phase == 'confirmation' else 'score_tum_panel_generic'
            self.stage('score_' + phase, [scores, folder / 'summary.json'],
                lambda phase=phase, scorer=scorer, score_args=score_args: self.original('score_' + phase, scorer, score_args, False), [panel, *model_inputs])
            self.stage('analyze_' + phase, [results[phase], folder / 'analysis.json'],
                lambda phase=phase, panel=panel, scores=scores, folder=folder: self.original('analyze_' + phase,
                    'analyze_tum_confirmation', ['--panel', panel, '--results', scores, '--out', folder / 'analysis.json']),
                [candidate, panel, scores])
            previous = panel
        expansion = self.run / 'artifacts/tum_expansion'
        final_ledger = self.run / 'receipts/report_expansion_axis_ledger.json'
        def report():
            self.original('report_expansion', 'report_tum_expansion')
            shutil.copyfile(self.run / 'axis_ledger.json', final_ledger)
        self.stage('report_expansion', [expansion / 'expanded_metrics.json', expansion / 'expanded_finding_report.md', final_ledger],
            report,
            [results['expansion'], expansion / 'analysis.json'])
        shutil.copyfile(final_ledger, self.run / 'axis_ledger.json')
        assert self.completed == STAGES
        dump(self.run / 'workflow_receipt.json', {
            'completed': True, 'mode': 'raw_images_to_CONCH_predictions', 'stages': self.completed,
            'environment': self.environment, 'pipeline_fingerprint': self.fingerprint,
            'dataset_revision': DATA_REVISION, 'source_revision': SOURCE_REVISION,
            'checkpoint_revision': CHECKPOINT_REVISION,
            'result_hashes': {str(p): digest(p) for p in [*results.values(),
                self.run / 'artifacts/tum_confirmation/analysis.json',
                expansion / 'analysis.json', expansion / 'expanded_metrics.json']},
            'interpretation_boundary': 'Original report script contains historical fixed prose; assess regenerated numeric curves separately. Original agent determinations remain historical.',
        })
        verified_results(self.run)
        print('Completed original raw-image workflow:', self.run, flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--run-dir', type=Path, default=ROOT / 'generated/original-workflow')
    parser.add_argument('--inference-python', type=Path,
                        default=Path(os.environ.get('CONCH_INFERENCE_PYTHON', str(ROOT / '.venv-inference/bin/python'))))
    parser.add_argument('--numeric-site', type=Path)
    parser.add_argument('--allow-cpu', action='store_true')
    args = parser.parse_args()
    if not args.run:
        print(json.dumps({'stages': STAGES, 'run_dir': str(args.run_dir.resolve()),
              'inference_python': str(args.inference_python), 'dataset_revision': DATA_REVISION,
              'source_revision': SOURCE_REVISION, 'checkpoint_revision': CHECKPOINT_REVISION,
              'downloaded_target_shards': CRC_SHARDS + TUM_SHARDS,
              'reference_images': 1800, 'target_images': 12980, 'batch_size': 128,
              'requires': ['Python 3.11 inference environment via setup_inference.py',
                           'CONCH access accepted and HF_TOKEN/login available',
                           'git, network, disk space for seven image shards and 802 MB checkpoint',
                           'CUDA GPU (or explicit --allow-cpu); reference numeric-site installed'],
              'archived_target_score_fallback': False}, indent=2))
        return
    if not args.numeric_site:
        parser.error('--run requires --numeric-site (requirements_reference.txt installation).')
    Pipeline(args.run_dir, args.inference_python, args.numeric_site, args.allow_cpu).execute()


if __name__ == '__main__':
    main()
