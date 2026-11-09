"""Run visible notebook cells in a selected interpreter; no analysis code lives here."""
import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import time

import nbformat
from nbclient import NotebookClient
from jupyter_client.kernelspec import KernelSpecManager


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('notebook', type=Path)
    parser.add_argument('--cwd', type=Path)
    parser.add_argument('--python', default=sys.executable)
    parser.add_argument('--timeout', type=int, default=86400)
    args = parser.parse_args()
    notebook = args.notebook.resolve()
    working = (args.cwd or notebook.parent).resolve()
    # Preserve a virtual environment's Python symlink: resolving it can select
    # the base interpreter and lose the environment's installed packages.
    interpreter = (str(Path(args.python).expanduser().absolute()) if '/' in args.python
                   else shutil.which(args.python))
    if not interpreter or not Path(interpreter).is_file():
        parser.error('Notebook interpreter was not found: ' + args.python)
    book = nbformat.read(notebook, as_version=4)
    started = time.monotonic()
    error = None
    with tempfile.TemporaryDirectory(prefix='spectra-inline-kernel-') as temporary:
        kernel = Path(temporary) / 'inline-python'
        kernel.mkdir()
        (kernel / 'kernel.json').write_text(json.dumps({
            'argv': [interpreter, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
            'display_name': 'Inline analysis', 'language': 'python',
            'env': {'MPLCONFIGDIR': str(Path(temporary) / 'matplotlib'),
                    'IPYTHONDIR': str(Path(temporary) / 'ipython')}}))
        manager = KernelSpecManager(kernel_dirs=[temporary])
        client = NotebookClient(book, kernel_name='inline-python', timeout=args.timeout,
                                resources={'metadata': {'path': str(working)}}, allow_errors=False)
        client.km = client.create_kernel_manager()
        client.km.kernel_spec_manager = manager
        try:
            client.execute()
        except Exception as caught:
            error = f'{type(caught).__name__}: {caught}'
    record = {'completed': error is None, 'error': error, 'host': socket.gethostname(),
              'python': interpreter, 'working_directory': str(working),
              'elapsed_seconds': round(time.monotonic() - started, 3)}
    book.metadata['analysis_execution'] = record
    book.metadata.kernelspec = {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}
    nbformat.write(book, notebook)
    print(json.dumps(record, indent=2), flush=True)
    if error:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
