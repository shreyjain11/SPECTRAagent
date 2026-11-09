"""Validate saved outputs and export syntax-checkable cells; HTML is optional."""
import argparse
import ast
import hashlib
import json
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--html', action='store_true', help='Also create ignored local HTML previews')
    args = parser.parse_args()
    if args.html:
        from nbconvert import HTMLExporter
        exporter = HTMLExporter(template_name='lab')
        (ROOT / 'html').mkdir(exist_ok=True)
    (ROOT / 'code').mkdir(exist_ok=True)
    records = []
    for path in sorted((ROOT / 'notebooks').glob('*.ipynb')):
        notebook = nbformat.read(path, as_version=4)
        nbformat.validate(notebook)
        cells = [c for c in notebook.cells if c.cell_type == 'code']
        errors = [o for c in cells for o in c.outputs if o.output_type == 'error']
        assert not errors and all(c.execution_count is not None for c in cells), path
        assert notebook.metadata.recovery_execution.completed, path
        charts = sum('image/png' in o.get('data', {}) for c in cells for o in c.outputs)
        source = ''.join(f'# Notebook cell {i}\n{c.source.rstrip()}\n\n'
                         for i, c in enumerate(notebook.cells, 1) if c.cell_type == 'code')
        ast.parse(source)
        export = ROOT / 'code' / (path.stem + '.py')
        export.write_text(source)
        if args.html:
            body, _ = exporter.from_notebook_node(notebook)
            assert body.count('src="data:image/png;base64') == charts
            (ROOT / 'html' / (path.stem + '.html')).write_text(body)
        records.append({'notebook': str(path.relative_to(ROOT)),
                        'analysis_id': notebook.metadata.primary_analysis_id,
                        'code_cells': len(cells), 'executed_code_cells': len(cells),
                        'saved_chart_images': charts, 'errors': 0,
                        'execution': dict(notebook.metadata.recovery_execution),
                        'notebook_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'code_export': str(export.relative_to(ROOT)),
                        'code_sha256': hashlib.sha256(export.read_bytes()).hexdigest()})
    (ROOT / 'notebook_validation.json').write_text(json.dumps(records, indent=2) + '\n')
    print(json.dumps({'notebooks': len(records), 'code_cells': sum(r['code_cells'] for r in records),
                      'saved_chart_images': sum(r['saved_chart_images'] for r in records), 'errors': 0}))


if __name__ == '__main__':
    main()
