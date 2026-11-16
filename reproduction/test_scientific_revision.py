"""Focused scope and artifact-integrity tests for scientific revision receipts."""
import copy
import gzip
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from validate_scientific_revision import canonical, check_scientific_revision, code_cells


class ScientificRevisionTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.old = {'nbformat': 4, 'cells': [
            {'cell_type': 'markdown', 'source': ['# Example']},
            {'cell_type': 'code', 'source': ['x = 1'], 'execution_count': 1, 'outputs': []},
            {'cell_type': 'code', 'source': ['print(x)'], 'execution_count': 2,
             'outputs': [{'output_type': 'stream', 'name': 'stdout', 'text': ['1\n']}]},
        ]}
        self.book = copy.deepcopy(self.old)
        self.book['cells'][2]['source'] = ['print(x + 1)']
        self.book['cells'][2]['outputs'][0]['text'] = ['2\n']
        old_bytes = json.dumps(self.old).encode()
        self.put('old.ipynb.gz', gzip.compress(old_bytes, mtime=0))
        self.previous = {'analysis_id': 'example/test', 'completed': True,
                         'notebook': 'current.ipynb', 'html': 'current.html',
                         'notebook_sha256': hashlib.sha256(old_bytes).hexdigest(),
                         'html_sha256': hashlib.sha256(b'old HTML').hexdigest()}
        self.put_json('previous.json', self.previous)
        self.put('driver.py', b'x = 1\n')
        self.put('run.log', b'Executed cell 2\n')
        self.put('input.csv', b'x\n1\n')
        self.put('output.csv', b'y\n2\n')
        self.put('current.html', b'<p>2</p>')
        self.receipt = {'analysis_id': 'example/test', 'completed': True,
                        'notebook': 'current.ipynb', 'html': 'current.html',
                        'host': 'local', 'python': '3.11', 'elapsed_seconds': 1.,
                        'code_cells': 2, 'executed_cells': 1, 'errors': 0,
                        'execution_scope': 'selected_cells_reexecuted',
                        'checks': ['selected_code_cells_executed'],
                        'scientific_revision': {
                            'schema_version': 1, 'scientific_reexecution': True,
                            'mode': 'selected_cells',
                            'previous_execution_evidence': self.artifact('previous.json'),
                            'original_notebook_snapshot': {
                                **self.artifact('old.ipynb.gz'), 'compression': 'gzip',
                                'notebook_sha256': self.previous['notebook_sha256']}}}
        self.record = {
            'schema_version': 1, 'analysis_id': 'example/test',
            'scientific_reexecution': True, 'mode': 'selected_cells',
            'reason': 'Correct arithmetic in the displayed result.',
            'original_commit': 'a' * 40,
            'original_artifacts': {kind: {'path': self.previous[kind],
                'sha256': self.previous[kind + '_sha256']} for kind in ('notebook', 'html')},
            'executed_notebook_cells': [2],
            'execution': {'host': 'local', 'python': '3.11', 'elapsed_seconds': 1.,
                          'started_at': '2026-11-15T12:00:00+00:00',
                          'finished_at': '2026-11-15T12:00:01+00:00',
                          'command': 'python driver.py', 'driver': self.artifact('driver.py'),
                          'log': self.artifact('run.log')},
            'inputs': [{**self.artifact('input.csv'), 'role': 'Saved input records', 'rows': 1}],
            'output_artifacts': [self.artifact('output.csv')],
            'prerequisite_setup': {'script': self.artifact('driver.py'),
                                   'input_paths': ['input.csv'],
                                   'description': 'Restore x from the saved input.'},
            'dependency_scope': 'Only cell 2 reran; cell 1 is retained exactly.'}
        self.refresh()

    def tearDown(self):
        self.temp.cleanup()

    def put(self, path, data):
        (self.root / path).write_bytes(data)

    def put_json(self, path, data):
        self.put(path, json.dumps(data).encode())

    def digest(self, path):
        return hashlib.sha256((self.root / path).read_bytes()).hexdigest()

    def artifact(self, path):
        return {'path': path, 'sha256': self.digest(path)}

    def refresh(self):
        self.put_json('current.ipynb', self.book)
        self.record['original_code_cells'] = code_cells(self.old)
        self.record['published_code_cells'] = code_cells(self.book)
        self.record['changed_code_cells'] = [i for i, c in enumerate(self.book['cells'])
            if c['cell_type'] == 'code' and c != self.old['cells'][i]]
        self.record['executed_cell_evidence'] = [c for c in code_cells(self.book)
            if c['notebook_cell'] in self.record['executed_notebook_cells']]
        self.record['published_artifacts'] = {kind: self.artifact(self.receipt[kind])
                                             for kind in ('notebook', 'html')}
        for kind in ('notebook', 'html'):
            self.receipt[kind + '_sha256'] = self.digest(self.receipt[kind])
        self.put_json('record.json', self.record)
        self.receipt['scientific_revision']['record'] = self.artifact('record.json')

    def validate(self):
        return check_scientific_revision(self.receipt, self.book,
            lambda path: json.loads((self.root / path).read_text()), self.digest,
            lambda path: self.root / path)

    def test_valid_selected(self):
        self.assertEqual(self.validate()['executed_notebook_cells'], [2])

    def test_valid_full(self):
        self.receipt['scientific_revision']['mode'] = self.record['mode'] = 'full_notebook'
        self.receipt['execution_scope'] = 'full_notebook_reexecuted'
        self.receipt['executed_cells'] = 2
        self.record['executed_notebook_cells'] = [1, 2]
        del self.record['prerequisite_setup']
        self.refresh()
        self.assertEqual(self.validate()['mode'], 'full_notebook')

    def test_unexecuted_source_or_output_cannot_change(self):
        for field, value in [('source', ['x = 3']), ('outputs', [{'output_type': 'stream', 'text': ['3']}])]:
            with self.subTest(field=field):
                original = copy.deepcopy(self.book['cells'][1])
                self.book['cells'][1][field] = value
                self.refresh()
                with self.assertRaisesRegex(AssertionError, 'Unexecuted scientific cell'):
                    self.validate()
                self.book['cells'][1] = original

    def test_full_mode_must_execute_all(self):
        self.receipt['scientific_revision']['mode'] = self.record['mode'] = 'full_notebook'
        self.receipt['execution_scope'] = 'full_notebook_reexecuted'
        self.refresh()
        with self.assertRaisesRegex(AssertionError, 'every code cell'):
            self.validate()

    def test_partial_cannot_claim_full_execution(self):
        self.receipt['checks'].append('all_code_cells_executed')
        with self.assertRaisesRegex(AssertionError, 'not a fresh full-notebook'):
            self.validate()

    def test_changed_input_is_rejected(self):
        self.put('input.csv', b'x\n9\n')
        with self.assertRaisesRegex(AssertionError, 'Artifact hash mismatch'):
            self.validate()

    def test_original_notebook_must_match_previous_receipt(self):
        self.put('old.ipynb.gz', gzip.compress(json.dumps(self.book).encode(), mtime=0))
        self.receipt['scientific_revision']['original_notebook_snapshot'].update(self.artifact('old.ipynb.gz'))
        with self.assertRaises(AssertionError):
            self.validate()

    def test_prerequisites_must_bind_consumed_inputs(self):
        self.record['prerequisite_setup']['input_paths'] = ['unknown.csv']
        self.refresh()
        with self.assertRaises(AssertionError):
            self.validate()

    def test_current_execution_identity_must_match(self):
        self.receipt['host'] = 'copied-old-host'
        with self.assertRaises(AssertionError):
            self.validate()

    def test_error_output_is_rejected(self):
        self.book['cells'][2]['outputs'] = [{'output_type': 'error', 'ename': 'ValueError'}]
        self.refresh()
        with self.assertRaisesRegex(AssertionError, 'Error output'):
            self.validate()

    def test_paths_cannot_escape_repository(self):
        self.record['inputs'][0]['path'] = '../input.csv'
        self.refresh()
        with self.assertRaises(AssertionError):
            self.validate()

    def prepare_direct(self):
        cell = self.book['cells'][2]
        cell['execution_count'] = None
        run = self.record['execution']
        run['engine'] = 'python_exec'
        cell['metadata'] = {'direct_execution': {
            'engine': 'python_exec', 'completed': True,
            'source_sha256': hashlib.sha256(''.join(cell['source']).encode()).hexdigest(),
            'outputs_sha256': canonical(cell['outputs']),
            'started_at': run['started_at'], 'finished_at': run['finished_at']}}
        direct = cell['metadata']['direct_execution']
        log = {'host': run['host'], 'python': run['python'],
               'driver_sha256': run['driver']['sha256'], 'full_notebook_reexecution': False,
               'cells': [{'notebook': 'reproduction/current.ipynb', 'cell_index': 2,
                          'source_sha256': direct['source_sha256'],
                          'outputs_sha256': direct['outputs_sha256'],
                          'before_outputs': self.old['cells'][2]['outputs'],
                          'after_outputs': cell['outputs'],
                          'started_at_utc': run['started_at'], 'duration_seconds': 1.}]}
        self.put_json('run.log', log)
        run['log'] = self.artifact('run.log')
        self.refresh()

    def test_valid_direct_python_execution(self):
        self.prepare_direct()
        self.assertEqual(self.validate()['executed_notebook_cells'], [2])

    def test_direct_source_log_must_match(self):
        self.prepare_direct()
        log = json.loads((self.root / 'run.log').read_text())
        log['cells'][0]['source_sha256'] = '0' * 64
        self.put_json('run.log', log)
        self.record['execution']['log'] = self.artifact('run.log')
        self.refresh()
        with self.assertRaises(AssertionError):
            self.validate()

    def test_null_count_requires_explicit_direct_engine(self):
        self.book['cells'][2]['execution_count'] = None
        self.refresh()
        with self.assertRaisesRegex(AssertionError, 'Missing execution count'):
            self.validate()

    def test_inline_review_only_accepts_declared_direct_cells(self):
        from integrate_inline import code_review
        self.prepare_direct()
        cells = []
        for section in range(1, 7):
            cells.extend([{'cell_type': 'markdown', 'source': [f'## {section}. Section']},
                          copy.deepcopy(self.book['cells'][2] if section == 1 else self.old['cells'][1])])
        book = {'cells': cells}
        with self.assertRaisesRegex(AssertionError, 'Unexecuted code cells'):
            code_review(book)
        code_review(book, direct_executed_cells=[1])
        book['cells'][3]['execution_count'] = None
        with self.assertRaisesRegex(AssertionError, 'Unexecuted code cells'):
            code_review(book, direct_executed_cells=[1])


if __name__ == '__main__':
    unittest.main()
