"""Execute published notebooks using their public input preparation cells."""
import argparse
import concurrent.futures
import datetime
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent


def execute(record, output, timeout):
    import nbformat
    from nbclient import NotebookClient
    notebook = ROOT / record['implementation']['notebook']
    book = nbformat.read(notebook, as_version=4)
    destination = output / (record['id'] + '.ipynb')
    destination.parent.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    result = {'id': record['id'], 'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    try:
        NotebookClient(book, timeout=timeout, kernel_name='python3', resources={
            'metadata': {'path': str(notebook.parent)},
        }).execute()
        result['executed_cells'] = len(book.cells)
        result['error'] = None
    except Exception as error:
        result['executed_cells'] = sum(cell.get('execution_count') is not None for cell in book.cells)
        result['error'] = str(error)[-5000:]
    nbformat.write(book, destination)
    result['seconds'] = round(time.monotonic() - started, 3)
    result['notebook'] = str(destination)
    print(json.dumps({'id': result['id'], 'seconds': result['seconds'], 'error': result['error']}), flush=True)
    destination.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def run_model(records, output, timeout):
    return [execute(record, output, timeout) for record in records]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--analysis', action='append', help='For example conch-opus-r2/test-01; repeat to select several.')
    selection.add_argument('--model', choices=['state', 'esmfold2', 'conch', 'alphamissense'])
    selection.add_argument('--all', action='store_true')
    parser.add_argument('--output', type=Path, default=ROOT / '.executions')
    parser.add_argument('--cell-timeout', type=int, default=1800)
    parser.add_argument('--workers', type=int, default=1, help='Number of model groups; notebooks within a model run sequentially.')
    args = parser.parse_args()
    groups = {}
    for path in sorted((ROOT / 'analyses').glob('*/*.json')):
        record = json.loads(path.read_text())
        model = Path(record['dataset_split']['input_inventory']).stem
        if args.analysis and record['id'] not in args.analysis:
            continue
        if args.model and model != args.model:
            continue
        groups.setdefault(model, []).append(record)
    if not groups:
        parser.error('No matching analysis records.')
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    # Bound native-library parallelism while several models execute concurrently.
    for variable in ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS']:
        os.environ.setdefault(variable, '1')
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as executor:
        futures = [executor.submit(run_model, records, output, args.cell_timeout) for records in groups.values()]
        results = [record for future in futures for record in future.result()]
    report = {'analyses': len(results), 'executed_without_error': sum(x['error'] is None for x in results), 'results': results}
    (output / 'execution.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items() if key != 'results'}, indent=2))
    return 1 if any(x['error'] for x in results) else 0


if __name__ == '__main__':
    sys.exit(main())
