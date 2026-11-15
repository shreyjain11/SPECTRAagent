"""Verify presentation edits without treating them as new scientific executions."""
import copy
import hashlib
import json


def sha_text(value):
    return hashlib.sha256(value.encode()).hexdigest()


def canonical(value):
    return sha_text(json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False))


def check_revision(receipt, book, read, digest):
    revision = receipt.get('presentation_revision')
    if not revision:
        return
    assert revision['scientific_reexecution'] is False
    for key in ('original_execution_evidence', 'correction_record'):
        item = revision[key]
        assert digest(item['path']) == item['sha256'], item['path']
    original = read(revision['original_execution_evidence']['path'])
    change = read(revision['correction_record']['path'])
    assert change['analysis_id'] == receipt['analysis_id'] == original['analysis_id']
    assert change['scientific_reexecution'] is False
    assert original['completed'] and original['host'] == receipt['host']
    assert original['executed_cells'] == receipt['executed_cells']
    state_style = 'original_artifacts' in change
    before = change['original_artifacts'] if state_style else {
        'notebook': change['original_notebook'], 'html': change['original_html']}
    after = change['published_artifacts'] if state_style else {
        'notebook': change['revised_notebook'], 'html': change['revised_html']}
    for kind in ('notebook', 'html'):
        assert before[kind]['sha256'] == original[kind + '_sha256']
        assert after[kind]['sha256'] == receipt[kind + '_sha256'] == digest(after[kind]['path'])
    prior = change['original_code_cells']
    published = change['published_code_cells'] if state_style else change['revised_code_cells']
    indices = [i for i, c in enumerate(book['cells']) if c['cell_type'] == 'code']
    assert len(indices) == len(prior) == len(published)
    display_change = change.get('changes', {}).get('display_only_change') if not state_style else None
    for i, old, now in zip(indices, prior, published):
        key = 'notebook_cell' if state_style else 'cell'
        assert old[key] == now[key] == i
        cell = book['cells'][i]
        assert old['execution_count'] == now['execution_count'] == cell['execution_count']
        assert sha_text(''.join(cell['source'])) == now['source_sha256']
        assert canonical(cell['outputs']) == now['outputs_sha256']
        if state_style:
            assert canonical(cell) == now['cell_sha256'] == old['cell_sha256']
        if display_change and i == display_change['cell']:
            # This exception is one documented closing-bold delimiter, not an
            # escape hatch for changes to scientific calculations or numbers.
            assert receipt['analysis_id'] == 'conch-kimi-r2/test-01'
            d = display_change
            assert d['source_replacement']['new'] == d['source_replacement']['old'].replace("+' ", "+'** ")
            assert d['new_source'] == d['old_source'].replace(d['source_replacement']['old'], d['source_replacement']['new'], 1)
            assert ''.join(cell['source']) == d['new_source']
            assert sha_text(d['old_source']) == old['source_sha256']
            assert d['new_output'] == d['old_output'].replace(d['output_replacement']['old'], d['output_replacement']['new'], 1)
            assert d['new_output'].replace('**', '') == d['old_output'].replace('**', '')
            restored = copy.deepcopy(cell['outputs'])
            output = restored[d['output_index']]['data'][d['mime_type']]
            assert ''.join(output) == d['new_output']
            restored[d['output_index']]['data'][d['mime_type']] = [d['old_output']] if isinstance(output, list) else d['old_output']
            assert canonical(restored) == old['outputs_sha256']
        else:
            assert old['source_sha256'] == now['source_sha256']
            assert old['outputs_sha256'] == now['outputs_sha256']
