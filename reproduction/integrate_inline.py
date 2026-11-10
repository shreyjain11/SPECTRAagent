"""Publish executed inline notebooks as the preferred analysis route.

Reads a supplied review directory; never runs scientific calculations. An entry
is promoted only when its execution evidence binds the exact notebook and HTML.
"""
import argparse
import ast
from collections import Counter
import hashlib
import html
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parent
FAMILIES = {'AlphaMissense': 'alphamissense', 'ESMFold2': 'esmfold2',
            'STATE': 'state', 'CONCH': 'conch'}


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_review(book):
    sections = []
    code = []
    current = None
    problems = []
    for index, cell in enumerate(book['cells']):
        source = ''.join(cell['source'])
        if cell['cell_type'] == 'markdown':
            match = re.search(r'^##\s+([1-6])[.)][^\n]*', source, re.M)
            if match:
                current = {'number': int(match[1]), 'heading': match[0],
                           'markdown_cell': index, 'code_cells': []}
                sections.append(current)
        elif cell['cell_type'] == 'code':
            code.append(cell)
            if current:
                current['code_cells'].append(index)
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    name = node.func.id if isinstance(node.func, ast.Name) else (
                        node.func.attr if isinstance(node.func, ast.Attribute) else '')
                    if ((isinstance(node.func, ast.Name) and name in {'exec', 'eval', '__import__'}) or name in {'spec_from_file_location', 'run_path'}):
                        problems.append(f'cell {index}: dynamic custom-code dispatch {name}')
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    modules = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or '']
                    if any(m.split('.')[0] in {'shared', 'run_pipeline', 'original_workflow', 'build_features',
                                               'run_analysis', 'reconstruct', 'current_implementation'} for m in modules):
                        problems.append(f'cell {index}: external analysis-module import')
            if re.search(r'(?:python|sys\.executable)[^\n]{0,220}[\w/-]+\.py[\'\"]', source):
                problems.append(f'cell {index}: review external Python script invocation')
    assert [s['number'] for s in sections] == list(range(1, 7)), 'Six numbered sections required'
    assert code and all(c.get('execution_count') is not None for c in code), 'Unexecuted code cells'
    assert not any(o.get('output_type') == 'error' for c in code for o in c.get('outputs', [])), 'Notebook error output'
    assert not problems, problems
    return sections, code


def evidence(source, family, notebook, identifier):
    path = source / notebook
    direct = path.with_suffix('.validation.json')
    candidates = []
    if direct.exists():
        candidates.append((direct, read(direct), None))
    for name in ['NONPRIMARY_VALIDATION.json', 'PRIMARY_OPUS_VALIDATION.json']:
        report = source / family / name
        if not report.exists():
            continue
        obj = read(report)
        for row in obj.get('entries', obj.get('notebooks', [])):
            if row.get('id', row.get('analysis_id')) == identifier:
                candidates.append((report, row, obj.get('host')))
    for report, row, outer_host in candidates:
        evidence_id = row.get('analysis_id', row.get('id'))
        if evidence_id:
            evidence_id = re.sub(r'/axis-(\d+)$', lambda m: '/test-' + m[1].zfill(2), evidence_id)
            if evidence_id != identifier:
                continue
        passed = row.get('completed') or row.get('passed') or str(row.get('status', '')).startswith('passed')
        host = row.get('host', row.get('execution_host', outer_host or ''))
        if not (passed and 'exxact05' in host.lower()):
            continue
        if row.get('notebook_sha256', row.get('sha256')) != sha(path):
            continue
        page = path.with_suffix('.html')
        if not page.exists() or row.get('html_sha256') != sha(page):
            continue
        if row.get('errors') or row.get('error_count') or row.get('failure') or row.get('error'):
            continue
        return report, row, host
    return None


def candidates(source, family, identifier, local_index):
    investigation, test = identifier.split('/')
    paths = [Path(family) / investigation / (test + '.ipynb')]
    number = int(test.split('-')[-1])
    paths.append(Path(family) / investigation / f'axis-{number}.ipynb')
    if identifier in local_index and local_index[identifier].get('notebook'):
        paths.insert(0, Path(local_index[identifier]['notebook']))
    safe = [p for p in paths if not p.is_absolute() and '..' not in p.parts and p.parts[0] == family
            and (source / p).resolve().is_relative_to(source) and (source / p).is_file()]
    return list(dict.fromkeys(safe))


def html_page(rows):
    counts = Counter(row['status'] for row in rows)
    body = ['<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
            '<title>Inline analysis notebooks</title><style>body{font:16px system-ui;max-width:1250px;margin:3rem auto;padding:0 1rem;color:#172332}table{border-collapse:collapse;width:100%}th,td{text-align:left;padding:.7rem;border-bottom:1px solid #dce2e8;vertical-align:top}th{background:#f2f6f9}a{color:#155c9b}.pending{color:#765316}</style>',
            '<h1>Inline analysis notebooks</h1><p>Acquisition, processing, axes and levels, model results, curves and controls, and calculated decisions are visible in six executable sections.</p>',
            '<p>' + html.escape('; '.join(f'{value} {key.replace("_", " ")}' for key, value in sorted(counts.items()))) + '.</p>',
            '<p>Open each result to inspect its calculated conclusion and limitations. Execution verifies that the displayed workflow ran; it does not guarantee a positive finding. Candidates without outcome measurements are identified explicitly.</p>',
            '<table><thead><tr><th>Investigation / axis</th><th>Status</th><th>Review</th></tr></thead><tbody>']
    for row in rows:
        links = ''
        if row.get('notebook'):
            links = ' · '.join(f'<a href="{html.escape(row[k].removeprefix("inline/"))}">{label}</a>' for k, label in [('html', 'Results and code'), ('notebook', 'Notebook'), ('validation', 'Execution evidence')])
        body.append('<tr><td>' + html.escape(row['id']) + '<br>' + html.escape(row['axis']) + '</td><td>' + html.escape(row['status'].replace('_', ' ')) + '</td><td>' + links + '</td></tr>')
    body.append('</tbody></table></html>')
    return '\n'.join(body)


def markdown_index(rows):
    lines = ['# Analysis notebook index', '',
             'Open a notebook to read its code, executed outputs, and section 6 decision. The HTML files provide a separate browser view after download. Pending entries have no verified notebook link.', '']
    for family in FAMILIES:
        lines += ['## ' + family, '', '| Investigation / axis | Status | Notebook and evidence |', '|---|---|---|']
        for row in rows:
            if row['model'] != family:
                continue
            links = ''
            if row['notebook']:
                links = ' · '.join(f"[{label}]({row[key].removeprefix('inline/')})" for key, label in [('notebook', 'Notebook'), ('html', 'HTML'), ('validation', 'Execution')])
            axis = row['axis'].replace('|', '\\|').replace('\n', ' ')
            lines.append(f"| `{row['id']}`<br>{axis} | {row['status'].replace('_', ' ')} | {links} |")
        lines.append('')
    return '\n'.join(lines)


def review_page(rows):
    counts = Counter(row['status'] for row in rows)
    lines = ['# Notebook execution review', '',
             'The catalog covers 143 entries across 28 investigations. Open the [notebook index](inline/INDEX.md) or [setup guide](inline/README.md) to review and run the notebooks.', '',
             f"**{counts['executed_inline']} analysis notebooks have completed on exxact05; {counts['documented_unperformed_candidate']} entry documents an unperformed candidate. {sum(v for k, v in counts.items() if k.startswith('pending'))} entries are pending verification.**", '',
             '| Model | Executed analyses | Unperformed candidates | Pending | Total |',
             '|---|---:|---:|---:|---:|']
    for family in FAMILIES:
        group = [row for row in rows if row['model'] == family]
        tally = Counter(row['status'] for row in group)
        pending = sum(v for k, v in tally.items() if k.startswith('pending'))
        lines.append(f"| {family} | {tally['executed_inline']} | {tally['documented_unperformed_candidate']} | {pending} | {len(group)} |")
    lines += ['', '## Review criteria', '',
              'Each preferred notebook places its custom calculation code in six numbered sections:', '',
              '1. Data source and acquisition.', '2. Data processing.',
              '3. Axis definition and level construction.', '4. Model results or released scores.',
              '5. Curves and controls.', '6. Calculated decision and explanation.', '',
              'Completed entries have executed cells, no error outputs, rendered results, and execution evidence matching the published notebook and HTML hashes. Input and eligibility screens explain where evaluation stopped. The unperformed membrane candidate has no model-performance claim.', '',
              'STATE and AlphaMissense notebooks identify the public individual scores they use. ESMFold2 and CONCH notebooks identify whether their results use released measurements or fresh inference. Model prediction caches are checked against the inputs and settings specified in the cells. Custom scientific calculations are visible inline.', '',
              'The registry and runner select the verified inline notebook by default. Section 6 supplies its calculated result. Pending entries cannot silently select a supporting implementation.', '',
              '## Validation', '',
              'Run `python reproduction/validate.py` from the repository root to check all 143 registry entries, preferred notebook hashes and section maps, included input manifests, and supporting artifact links. [Packaging checks](inline/PACKAGING_VALIDATION.json) also record the runner test on exxact05.', '']
    pending = [row for row in rows if row['status'].startswith('pending')]
    if pending:
        lines += ['## Pending executions', '',
                  'These entries are not published as verified inline analyses:', '']
        lines += [f"- `{row['id']}` — {row['axis']}" for row in pending]
        lines.append('')
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True, help='Directory containing the four model families and execution evidence.')
    args = parser.parse_args()
    source = args.source.expanduser().resolve()
    index = read(ROOT / 'index.json')
    status_path = source / 'REVIEW_STATUS.json'
    local_index = {r['id']: r for r in read(status_path)['notebooks']} if status_path.exists() else {}
    rows = []
    failures = []
    for investigation in index['investigations']:
        family = FAMILIES[investigation['model']]
        for entry in investigation['analyses']:
            identifier = entry['id']
            record_path = ROOT / entry['path']
            record = read(record_path)
            row = {'id': identifier, 'model': investigation['model'], 'axis': entry['axis'],
                   'status': 'pending_execution', 'notebook': None, 'html': None, 'validation': None}
            selected = None
            for relative in candidates(source, family, identifier, local_index):
                check = evidence(source, family, relative, identifier)
                if check:
                    selected = relative, check
                    break
            if selected:
                relative, (report_path, raw, host) = selected
                notebook = source / relative
                try:
                    book = read(notebook)
                    sections, code = code_review(book)
                    destination = ROOT / 'inline' / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(notebook, destination)
                    shutil.copyfile(notebook.with_suffix('.html'), destination.with_suffix('.html'))
                    prefix = str(destination.relative_to(ROOT).with_suffix(''))
                    normalized = {'analysis_id': identifier, 'notebook': prefix + '.ipynb',
                                  'html': prefix + '.html', 'completed': True, 'host': host,
                                  'code_cells': len(code), 'executed_cells': len(code), 'errors': 0,
                                  'notebook_sha256': sha(destination), 'html_sha256': sha(destination.with_suffix('.html')),
                                  'sections': sections, 'cell_index_base': 0, 'execution_evidence_source_sha256': sha(report_path),
                                  'execution_evidence_entry_id': raw.get('analysis_id', raw.get('id', identifier)),
                                  'embedded_figures': sum('image/png' in o.get('data', {}) for c in code for o in c.get('outputs', [])),
                                  'checks': ['notebook_and_html_hash_match_execution_evidence', 'all_code_cells_executed',
                                             'no_error_outputs', 'six_sections_and_executed_inline_code', 'inline_code_static_check'],
                                  'result_location': {'section': 6, 'code_cells': sections[-1]['code_cells']},
                                  'input_manifests': []}
                    for input_file in sorted((notebook.parent / 'inputs').rglob('*')):
                        if not input_file.is_file():
                            continue
                        if input_file.suffix not in {'.json', '.csv', '.tsv', '.txt', '.md'} or input_file.stat().st_size > 2_000_000:
                            raise ValueError('Review input asset before publication: ' + input_file.name)
                        target = destination.parent / input_file.relative_to(notebook.parent)
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copyfile(input_file, target)
                        normalized['input_manifests'].append({'path': str(target.relative_to(ROOT)),
                                                             'sha256': sha(target), 'bytes': target.stat().st_size})
                    for field in ['elapsed_seconds', 'python']:
                        if field in raw:
                            normalized[field] = raw[field]
                    # These are calculation provenance receipts, not calculation inputs.
                    normalized['calculation_evidence'] = []
                    output_paths = raw.get('output_receipts', []) + ([raw['output_receipt']] if raw.get('output_receipt') else [])
                    for output in output_paths:
                        evidence_path = next((path for path in [source / family / output, notebook.parent / output]
                                              if path.is_file()), None)
                        if evidence_path is None:
                            continue
                        target = destination.parent / (destination.stem + '-evidence') / evidence_path.name
                        target.parent.mkdir(exist_ok=True)
                        shutil.copyfile(evidence_path, target)
                        normalized['calculation_evidence'].append({'path': str(target.relative_to(ROOT)), 'sha256': sha(target)})
                    if output_paths and local_index.get(identifier, {}).get('status') != 'Documented unperformed candidate':
                        for name in ['PUBLIC_SOURCE_SNAPSHOT_ASSET.json', 'PUBLIC_SOURCE_BOOTSTRAP_VALIDATION.json',
                                     'PARALLEL_SCORING_VALIDATION.json']:
                            evidence_path = notebook.parent / name
                            if evidence_path.is_file():
                                target = destination.parent / name
                                shutil.copyfile(evidence_path, target)
                                normalized['calculation_evidence'].append({'path': str(target.relative_to(ROOT)),
                                                                          'sha256': sha(target)})
                    receipt_path = destination.with_suffix('.execution.json')
                    write(receipt_path, normalized)
                    unperformed = local_index.get(identifier, {}).get('status') == 'Documented unperformed candidate'
                    row.update(status='documented_unperformed_candidate' if unperformed else 'executed_inline',
                               notebook=prefix + '.ipynb', html=prefix + '.html', validation=prefix + '.execution.json')
                    record['inline_implementation'] = {'format': 'inline_analysis_notebook',
                        'notebook': row['notebook'], 'html': row['html'], 'execution_evidence': row['validation'],
                        'published_notebook_sha256': normalized['notebook_sha256'],
                        'published_html_sha256': normalized['html_sha256'],
                        'code_cells': len(code), 'sections': sections,
                        'calculated_result': normalized['result_location'], 'status': row['status']}
                except Exception as error:
                    failures.append({'id': identifier, 'problem': str(error)})
                    row['status'] = 'pending_inline_check'
            if not row['notebook']:
                record.pop('inline_implementation', None)
            entry['supporting_notebook'] = record['implementation']['notebook']
            entry['notebook'] = row['notebook']
            entry['inline_status'] = row['status']
            record['preferred_route'] = 'inline_implementation'
            record['preferred_result'] = ({'notebook': row['notebook'], 'section': 6,
                                          'description': 'Calculated decision and explanation displayed by this notebook.'}
                                         if row['notebook'] else {'description': 'Inline notebook execution is pending.'})
            write(record_path, record)
            rows.append(row)
    for family in FAMILIES.values():
        for name in ['requirements.txt', 'requirements-cpu.txt', 'requirements-model.txt', 'requirements-primary.txt', 'requirements-shared.txt',
                     'CPU_ENVIRONMENT.json', 'MODEL_ENVIRONMENT.json', 'MODEL_SOURCE_REVISION_EQUIVALENCE.json', 'README.md', 'README.txt']:
            item = source / family / name
            if item.is_file():
                target = ROOT / 'inline' / family / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(item, target)
    active = {str(ROOT / row['notebook']) for row in rows if row['notebook']}
    for old in (ROOT / 'inline').glob('*/*/*.ipynb'):
        if str(old) not in active:
            for suffix in ['.ipynb', '.html', '.execution.json']:
                old.with_suffix(suffix).unlink(missing_ok=True)
    index['preferred_notebooks'] = 'inline/index.json'
    index['preferred_notebook_guide'] = 'inline/README.md'
    index['preferred_workflow_review'] = 'PR_REVIEW.md'
    index['preferred_notebook_format'] = 'inline_analysis_notebook'
    write(ROOT / 'index.json', index)
    result = {'schema_version': 1, 'scope': 'Six-section inline analysis workflows',
              'counts': dict(Counter(row['status'] for row in rows)), 'analyses': rows, 'checks_pending': failures}
    write(ROOT / 'inline/index.json', result)
    (ROOT / 'inline/index.html').write_text(html_page(rows))
    (ROOT / 'inline/INDEX.md').write_text(markdown_index(rows))
    (ROOT / 'PR_REVIEW.md').write_text(review_page(rows))
    print(json.dumps({'counts': result['counts'], 'checks_pending': failures}, indent=2))


if __name__ == '__main__':
    main()
