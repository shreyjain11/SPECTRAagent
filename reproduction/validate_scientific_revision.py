"""Validate a scientific correction without relabeling old outputs as a new run.

Version 1 schema is documented in SCIENTIFIC_REVISION_SCHEMA.md. Validation
checks recorded execution evidence and artifact identity; it does not execute
notebooks or establish the scientific validity of the chosen analysis.
"""
import copy
import gzip
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import PurePosixPath


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return _sha(json.dumps(value, sort_keys=True, separators=(',', ':'),
                           ensure_ascii=False).encode())


def code_cells(book):
    """Stable per-cell fingerprints for a revision record."""
    return [
        {'notebook_cell': i, 'execution_count': cell.get('execution_count'),
         'source_sha256': _sha(''.join(cell['source']).encode()),
         'outputs_sha256': canonical(cell.get('outputs', [])),
         'cell_sha256': canonical(cell)}
        for i, cell in enumerate(book['cells']) if cell['cell_type'] == 'code'
    ]


def _path(path):
    assert isinstance(path, str) and path, 'Missing artifact path'
    parsed = PurePosixPath(path)
    assert not parsed.is_absolute() and '..' not in parsed.parts, path
    assert '\\' not in path and '://' not in path, path
    return path


def _artifact(item, digest, file):
    path = _path(item['path'])
    assert re.fullmatch('[0-9a-f]{64}', item['sha256']), path
    assert digest(path) == item['sha256'], ('Artifact hash mismatch', path)
    if 'bytes' in item:
        assert type(item['bytes']) is int and item['bytes'] >= 0, path
        assert file(path).stat().st_size == item['bytes'], path
    return path


def _instant(value):
    assert isinstance(value, str)
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    assert parsed.tzinfo is not None, 'Execution time must include a timezone'
    return parsed


def check_direct_cell(cell):
    """A declared Python execution has evidence, not a fabricated kernel count."""
    assert cell.get('execution_count') is None, 'Python exec does not assign Jupyter execution counts'
    direct = cell['metadata']['direct_execution']
    assert direct['engine'] == 'python_exec' and direct['completed'] is True
    assert direct['source_sha256'] == _sha(''.join(cell['source']).encode())
    assert direct['outputs_sha256'] == canonical(cell.get('outputs', []))
    assert _instant(direct['finished_at']) >= _instant(direct['started_at'])
    return direct


def _check_previous_chain(receipt, read, digest, file, book):
    """Check archived presentation boundaries without using current file hashes.

    A previous receipt describes an earlier notebook/page. Its original paths
    can now point at corrected files, so use retained records and their hashes,
    not the current contents of the earlier publication paths.
    """
    seen = set()
    while receipt.get('presentation_revision') or receipt.get('scientific_revision'):
        assert not (receipt.get('presentation_revision') and receipt.get('scientific_revision')), 'Ambiguous archived revision'
        if receipt.get('presentation_revision'):
            rev = receipt['presentation_revision']
            assert rev['scientific_reexecution'] is False
            previous_item = rev['original_execution_evidence']
            change_item = rev['correction_record']
            previous_path = _artifact(previous_item, digest, file)
            change = read(_artifact(change_item, digest, file))
            before = change.get('original_artifacts') or {
                'notebook': change['original_notebook'], 'html': change['original_html']}
            after = change.get('published_artifacts') or {
                'notebook': change['revised_notebook'], 'html': change['revised_html']}
            # Validate the prior code-preservation proof against the retained
            # original notebook. Its old publication paths now contain revised
            # files, so only those two artifact digests use the archived boundary.
            from validate_presentation import check_revision
            old_boundaries = {item['path']: item['sha256'] for item in after.values()}
            check_revision(receipt, book, read,
                           lambda path: old_boundaries[path] if path in old_boundaries else digest(path))
            changes = change.get('changes', {})
            display = changes.get('display_only_change') if isinstance(changes, dict) else None
            if display:
                book = copy.deepcopy(book)
                cell = book['cells'][display['cell']]
                cell['source'] = display['old_source']
                out = cell['outputs'][display['output_index']]['data']
                existing = out[display['mime_type']]
                out[display['mime_type']] = [display['old_output']] if isinstance(existing, list) else display['old_output']
        else:
            rev = receipt['scientific_revision']
            assert rev['schema_version'] == 1 and rev['scientific_reexecution'] is True
            previous_path = _artifact(rev['previous_execution_evidence'], digest, file)
            change = read(_artifact(rev['record'], digest, file))
            before, after = change['original_artifacts'], change['published_artifacts']
            snapshot = rev['original_notebook_snapshot']
            snapshot_path = _artifact(snapshot, digest, file)
            assert snapshot['compression'] == 'gzip'
            snapshot_bytes = gzip.decompress(file(snapshot_path).read_bytes())
            assert _sha(snapshot_bytes) == snapshot['notebook_sha256'] == before['notebook']['sha256']
            assert change['published_code_cells'] == code_cells(book)
            book = json.loads(snapshot_bytes)
            assert change['original_code_cells'] == code_cells(book)
        assert previous_path not in seen, 'Cyclic execution evidence'
        seen.add(previous_path)
        previous = read(previous_path)
        assert previous['analysis_id'] == receipt['analysis_id'] == change['analysis_id']
        for kind in ('notebook', 'html'):
            assert before[kind]['sha256'] == previous[kind + '_sha256']
            assert after[kind]['sha256'] == receipt[kind + '_sha256']
        receipt = previous
    assert receipt.get('completed') is True, 'Original execution did not complete'
    return len(seen)


def check_scientific_revision(receipt, book, read, digest, file):
    """Check the explicit full/selected execution branch; return its scope."""
    rev = receipt['scientific_revision']
    assert not receipt.get('presentation_revision'), 'New scientific receipt cannot retain a stale top-level presentation revision'
    assert rev['schema_version'] == 1 and rev['scientific_reexecution'] is True
    mode = rev['mode']
    assert mode in ('full_notebook', 'selected_cells')
    expected_scope = {'full_notebook': 'full_notebook_reexecuted',
                      'selected_cells': 'selected_cells_reexecuted'}[mode]
    assert receipt['execution_scope'] == expected_scope
    assert not receipt.get('presentation_note'), 'Remove the obsolete presentation-only note from the new scientific receipt'
    if mode == 'selected_cells':
        assert 'all_code_cells_executed' not in receipt.get('checks', []), 'Selected execution is not a fresh full-notebook execution'
    previous = read(_artifact(rev['previous_execution_evidence'], digest, file))
    record = read(_artifact(rev['record'], digest, file))
    assert record['schema_version'] == 1 and record['scientific_reexecution'] is True
    assert record['mode'] == mode
    run = record['execution']
    engine = run.get('engine', 'jupyter')
    assert engine in ('jupyter', 'python_exec'), 'Unsupported scientific execution engine'
    if engine == 'python_exec':
        assert mode == 'selected_cells', 'Direct Python execution is supported only for explicitly selected cells'
    assert record['analysis_id'] == receipt['analysis_id'] == previous['analysis_id']
    assert isinstance(record['reason'], str) and record['reason'].strip()
    assert re.fullmatch('[0-9a-f]{40}', record['original_commit'])

    snapshot = rev['original_notebook_snapshot']
    snapshot_path = _artifact(snapshot, digest, file)
    assert snapshot['compression'] == 'gzip'
    original_bytes = gzip.decompress(file(snapshot_path).read_bytes())
    assert _sha(original_bytes) == snapshot['notebook_sha256'] == previous['notebook_sha256']
    original = json.loads(original_bytes)
    assert original['nbformat'] == book['nbformat'] == 4
    for kind in ('notebook', 'html'):
        assert record['original_artifacts'][kind]['path'] == previous[kind]
        assert record['original_artifacts'][kind]['sha256'] == previous[kind + '_sha256']
        published = record['published_artifacts'][kind]
        assert _artifact(published, digest, file) == receipt[kind]
        assert published['sha256'] == receipt[kind + '_sha256']

    before, after = code_cells(original), code_cells(book)
    assert record['original_code_cells'] == before
    assert record['published_code_cells'] == after
    indices = [row['notebook_cell'] for row in after]
    executed = record['executed_notebook_cells']
    assert isinstance(executed, list) and executed
    assert all(type(i) is int for i in executed)
    assert executed == sorted(set(executed)) and set(executed) <= set(indices)
    assert receipt['code_cells'] == len(indices)
    assert receipt['executed_cells'] == len(executed)
    assert receipt['completed'] is True and receipt['errors'] == 0
    if mode == 'full_notebook':
        assert executed == indices, 'Full-notebook mode must execute every code cell'
    else:
        assert len(executed) < len(indices), 'Use full_notebook mode when all code cells execute'
        assert len(original['cells']) == len(book['cells']), 'Selected execution cannot insert or remove cells'
        assert [c['cell_type'] for c in original['cells']] == [c['cell_type'] for c in book['cells']], 'Selected execution cannot change cell types'
    changed = []
    for i in indices:
        cell = book['cells'][i]
        assert not any(o.get('output_type') == 'error' for o in cell.get('outputs', [])), ('Error output', i)
        different = (i >= len(original['cells']) or original['cells'][i] != cell)
        if different:
            changed.append(i)
            assert i in executed, ('Unexecuted scientific cell changed', i)
        if i in executed:
            if engine == 'python_exec':
                check_direct_cell(cell)
            else:
                assert type(cell.get('execution_count')) is int and cell['execution_count'] > 0, ('Missing execution count', i)
        elif mode == 'selected_cells':
            assert cell == original['cells'][i], ('Unexecuted scientific cell changed', i)
    assert record['changed_code_cells'] == changed
    execution_cells = record['executed_cell_evidence']
    assert execution_cells == [row for row in after if row['notebook_cell'] in executed]

    assert isinstance(run['host'], str) and run['host'].strip()
    assert isinstance(run['python'], str) and run['python'].strip()
    assert run['host'] == receipt['host'] and run['python'] == receipt['python']
    elapsed = run['elapsed_seconds']
    assert isinstance(elapsed, (int, float)) and not isinstance(elapsed, bool)
    assert math.isfinite(elapsed) and elapsed >= 0
    assert elapsed == receipt['elapsed_seconds']
    started, finished = _instant(run['started_at']), _instant(run['finished_at'])
    assert finished >= started
    assert elapsed <= (finished - started).total_seconds() + 5, 'Elapsed time exceeds recorded interval'
    assert isinstance(run['command'], str) and run['command'].strip()
    for name in ('driver', 'log'):
        _artifact(run[name], digest, file)
    if engine == 'python_exec':
        log = read(run['log']['path'])
        assert log['host'] == run['host'] and log['python'] == run['python']
        assert log['driver_sha256'] == run['driver']['sha256']
        assert log['full_notebook_reexecution'] is False
        logged = [entry for entry in log['cells']
                  if entry['notebook'] == 'reproduction/' + receipt['notebook']]
        assert sorted(entry['cell_index'] for entry in logged) == executed
        for entry in logged:
            i = entry['cell_index']
            cell = book['cells'][i]
            direct = check_direct_cell(cell)
            assert entry['source_sha256'] == direct['source_sha256']
            assert entry['outputs_sha256'] == direct['outputs_sha256']
            assert entry['after_outputs'] == cell.get('outputs', [])
            assert entry['before_outputs'] == original['cells'][i].get('outputs', [])
            assert _instant(entry['started_at_utc']) == _instant(direct['started_at'])
            duration = entry['duration_seconds']
            assert isinstance(duration, (int, float)) and math.isfinite(duration) and duration >= 0
            measured = (_instant(direct['finished_at']) - _instant(direct['started_at'])).total_seconds()
            assert abs(duration - measured) <= 2e-6, 'Direct-cell timing differs from original execution log'
            assert started <= _instant(direct['started_at']) <= _instant(direct['finished_at']) <= finished

    inputs = record['inputs']
    assert inputs, 'A scientific correction must identify the data consumed'
    assert len({entry['path'] for entry in inputs}) == len(inputs)
    for entry in inputs:
        _artifact(entry, digest, file)
        assert isinstance(entry['role'], str) and entry['role'].strip()
        if 'rows' in entry:
            assert type(entry['rows']) is int and entry['rows'] >= 0
    if mode == 'selected_cells':
        setup = record['prerequisite_setup']
        _artifact(setup['script'], digest, file)
        assert setup['input_paths'] and set(setup['input_paths']) <= {entry['path'] for entry in inputs}
        assert isinstance(setup['description'], str) and setup['description'].strip()
    outputs = record['output_artifacts']
    assert outputs, 'A scientific correction must identify regenerated artifacts'
    assert len({entry['path'] for entry in outputs}) == len(outputs)
    for entry in outputs:
        _artifact(entry, digest, file)
    assert isinstance(record['dependency_scope'], str) and record['dependency_scope'].strip()
    chain_depth = _check_previous_chain(previous, read, digest, file, original)
    return {'mode': mode, 'executed_notebook_cells': executed,
            'changed_code_cells': changed, 'prior_revision_depth': chain_depth,
            'original_notebook_sha256': previous['notebook_sha256']}
