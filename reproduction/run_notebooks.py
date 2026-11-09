"""Execute preferred notebooks, or the preserved public-bundle implementations.

Each run writes an output copy, leaving the published notebook unchanged. Use
the documented model environments; --model-python can select a different
notebook interpreter for each model in a mixed selection.
"""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from prepare_inputs import public_bundle_implementation, record_model

ROOT = Path(__file__).resolve().parent


def selected_implementation(record, implementation='preferred'):
    if implementation == 'public-bundle':
        return public_bundle_implementation(record)
    return record['implementation']


def execute(record, output, timeout, implementation='preferred', python=None,
            original_workflow=False):
    import nbformat
    selected = selected_implementation(record, implementation)
    notebook = ROOT / selected['notebook']
    book = nbformat.read(notebook, as_version=4)
    destination = output / (record['id'] + '.ipynb')
    if destination.resolve() == notebook.resolve():
        raise ValueError('Execution output must not overwrite the published notebook.')
    destination.parent.mkdir(parents=True, exist_ok=True)
    # A failed run must not present saved historical outputs as new execution.
    for cell in book.cells:
        if cell.cell_type == 'code':
            cell.execution_count = None
            cell.outputs = []
    book.metadata.pop('recovery_execution', None)
    nbformat.write(book, destination)
    started = time.monotonic()
    result = {'id': record['id'], 'model': record_model(record),
              'implementation': implementation, 'source_notebook': selected['notebook'],
              'source_notebook_sha256': hashlib.sha256(notebook.read_bytes()).hexdigest(),
              'python': python or sys.executable,
              'original_workflow_requested': original_workflow,
              'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    command = [sys.executable, str(ROOT / 'primary' / 'execute_notebook.py'),
               str(destination), '--cwd', str(notebook.parent),
               '--python', result['python'], '--timeout', str(timeout)]
    if original_workflow:
        command.append('--original-workflow')
    try:
        completed = subprocess.run(command, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, check=False)
        destination.with_suffix('.log').write_text(completed.stdout)
        executed = nbformat.read(destination, as_version=4)
        receipt = executed.metadata.get('recovery_execution', {})
        result['executed_cells'] = sum(cell.cell_type == 'code' and
                                      cell.get('execution_count') is not None
                                      for cell in executed.cells)
        result['error'] = None if completed.returncode == 0 and receipt.get('completed') else (
            receipt.get('error') or completed.stdout[-5000:] or
            f'Notebook runner exited with status {completed.returncode}')
    except Exception as error:
        result['executed_cells'] = 0
        result['error'] = str(error)[-5000:]
    result['seconds'] = round(time.monotonic() - started, 3)
    result['notebook'] = str(destination)
    print(json.dumps({'id': result['id'], 'seconds': result['seconds'], 'error': result['error']}), flush=True)
    destination.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def run_model(records, output, timeout, implementation='preferred', python=None,
              original_workflow=False):
    return [execute(record, output, timeout, implementation, python, original_workflow)
            for record in records]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--analysis', action='append', help='For example conch-opus-r2/test-01; repeat to select several.')
    selection.add_argument('--model', choices=['state', 'esmfold2', 'conch', 'alphamissense'])
    selection.add_argument('--all', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / '.executions')
    parser.add_argument('--cell-timeout', type=int, default=1800)
    parser.add_argument('--workers', type=int, default=1, help='Number of model groups; notebooks within a model run sequentially.')
    parser.add_argument('--implementation', choices=['preferred', 'public-bundle'],
                        default='preferred', help='Preferred uses recovered primary notebooks where available; public-bundle uses the original 143 code-only notebooks.')
    parser.add_argument('--primary-only', action='store_true', help='Limit the selection to the 44 recovered primary workflows.')
    parser.add_argument('--python', default=sys.executable, help='Notebook Python interpreter; defaults to this interpreter.')
    parser.add_argument('--model-python', action='append', default=[], metavar='MODEL=PYTHON',
                        help='Override the notebook interpreter for one model; repeat for mixed environments.')
    parser.add_argument('--original-workflow', action='store_true',
                        help='Run the full raw-data/model chain for selected primary ESMFold2 or CONCH notebooks. Downloads and model resources are required.')
    args = parser.parse_args()
    interpreters = {}
    for value in args.model_python:
        model, separator, python = value.partition('=')
        if not separator or model not in {'state', 'esmfold2', 'conch', 'alphamissense'} or not python:
            parser.error('--model-python must be MODEL=PYTHON for one of the four model names.')
        interpreters[model] = python
    groups = {}
    for path in sorted((ROOT / 'analyses').glob('*/*.json')):
        record = json.loads(path.read_text())
        model = record_model(record)
        if args.analysis and record['id'] not in args.analysis:
            continue
        if args.model and model != args.model:
            continue
        if args.primary_only and not record.get('primary_recovery'):
            continue
        groups.setdefault(model, []).append(record)
    if not groups:
        parser.error('No matching analysis records.')
    if args.analysis:
        found = {record['id'] for records in groups.values() for record in records}
        missing = set(args.analysis) - found
        if missing:
            parser.error('No matching selected analysis: ' + ', '.join(sorted(missing)))
    if args.original_workflow:
        unsupported = [record['id'] for model, records in groups.items() for record in records
                       if args.implementation != 'preferred' or
                       not record.get('primary_recovery') or model not in {'esmfold2', 'conch'}]
        if unsupported:
            parser.error('--original-workflow requires preferred primary ESMFold2/CONCH notebooks; use --primary-only with --model or select individual analyses. Unsupported: ' + ', '.join(unsupported))
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    # Bound native-library parallelism while several models execute concurrently.
    for variable in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS']:
        os.environ.setdefault(variable, '1')
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as executor:
        futures = [executor.submit(run_model, records, output, args.cell_timeout,
                                   args.implementation, interpreters.get(model, args.python),
                                   args.original_workflow)
                   for model, records in groups.items()]
        results = [record for future in futures for record in future.result()]
    report = {'implementation': args.implementation,
              'original_workflow_requested': args.original_workflow,
              'analyses': len(results), 'executed_without_error': sum(x['error'] is None for x in results), 'results': results}
    (output / 'execution.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'results'}, indent=2))
    return 1 if any(x['error'] for x in results) else 0


if __name__ == '__main__':
    sys.exit(main())
