"""Synthetic notebooks exist only inside temporary test directories."""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import struct
import zlib
from html.parser import HTMLParser

MODULE = Path(__file__).resolve().parents[1] / 'report.py'
spec = importlib.util.spec_from_file_location('investigation_report', MODULE)
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)
# A one-pixel fixture only; it is never used in an investigation report.
def png_chunk(kind, payload):
    return struct.pack('>I', len(payload)) + kind + payload + struct.pack('>I', zlib.crc32(kind + payload))


PNG = (b'\x89PNG\r\n\x1a\n' + png_chunk(b'IHDR', struct.pack('>IIBBBBB', 1, 1, 8, 2, 0, 0, 0))
       + png_chunk(b'IDAT', zlib.compress(b'\x00\xff\xff\xff')) + png_chunk(b'IEND', b''))


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.sequence = self.root / 'sequence.json'
        self.doc = {'title': 'Synthetic unit test', 'scope': 'Temporary synthetic fixture; not research evidence.',
                    'expected_axis_ids': ['axis-a', 'axis-b'],
                    'axes': [self.axis('axis-a', 1), self.axis('axis-b', 2)]}
        self.save()

    def tearDown(self):
        self.directory.cleanup()

    def save(self):
        self.sequence.write_text(json.dumps(self.doc))

    def axis(self, identifier, hour):
        cells = []
        for section in range(1, 7):
            cells += [{'cell_type': 'markdown', 'metadata': {}, 'source': f'## {section}. Section {section}'}]
            outputs = []
            if section == 5:
                outputs = [{'output_type': 'display_data', 'metadata': {},
                            'data': {'image/png': base64.b64encode(PNG).decode()}}]
            cells += [{'cell_type': 'code', 'metadata': {}, 'source': f'value = {section}',
                       'execution_count': section, 'outputs': outputs}]
        notebook = self.root / f'{identifier}.ipynb'
        notebook.write_text(json.dumps({'nbformat': 4, 'nbformat_minor': 4, 'metadata': {}, 'cells': cells}))
        start, end = f'2026-01-01T{hour:02}:00:00Z', f'2026-01-01T{hour:02}:01:00Z'
        receipt = {'notebook_sha256': hashlib.sha256(notebook.read_bytes()).hexdigest(),
                   'started_at': start, 'finished_at': end, 'executed_cells': 6,
                   'completed': True, 'errors': 0, 'engine': 'synthetic-fixture'}
        (self.root / f'{identifier}.execution.json').write_text(json.dumps(receipt))
        return {'id': identifier, 'title': identifier, 'notebook': notebook.name,
                'execution': f'{identifier}.execution.json', 'started_at': start, 'finished_at': end,
                'performed': True, 'sources': [{'url': 'https://example.org/fixture', 'role': 'Synthetic test input'}],
                'result': 'Synthetic fixture result.', 'curve': {'cell': 9, 'output': 0}}

    def assert_invalid(self, phrase):
        self.save()
        with self.assertRaisesRegex(report.ReportError, phrase):
            report.validate(self.sequence)

    def test_ledger_omission_rejected(self):
        self.doc['axes'].pop()
        self.assert_invalid('omitted, added, or reordered')

    def test_duplicate_id_rejected(self):
        self.doc['axes'][1]['id'] = 'axis-a'
        self.assert_invalid('Duplicate axis')

    def test_order_differs_from_ledger_rejected(self):
        self.doc['axes'].reverse()
        self.assert_invalid('omitted, added, or reordered')

    def test_false_chronology_rejected(self):
        self.doc['axes'].reverse()
        self.doc['expected_axis_ids'].reverse()
        self.assert_invalid('contradicts recorded start times')

    def test_missing_curve_rejected(self):
        self.doc['axes'][0]['curve'] = {'cell': 1, 'output': 0}
        self.assert_invalid('PNG output is missing')

    def test_mismatched_execution_time_rejected(self):
        self.doc['axes'][0]['started_at'] = '2026-01-01T00:00:00Z'
        self.assert_invalid('times differ')

    def test_notebook_hash_change_rejected(self):
        path = self.root / 'axis-a.ipynb'
        path.write_text(path.read_text() + '\n')
        self.assert_invalid('notebook hash differs')

    def test_source_http_rejected(self):
        self.doc['axes'][0]['sources'][0]['url'] = 'http://example.org/fixture'
        self.assert_invalid('must be HTTPS')

    def test_escape_rejected(self):
        self.doc['axes'][0]['notebook'] = '../outside.ipynb'
        self.assert_invalid('path leaves')

    def test_missing_section_code_rejected(self):
        path = self.root / 'axis-a.ipynb'
        nb = json.loads(path.read_text()); nb['cells'].pop(1); path.write_text(json.dumps(nb))
        receipt_path = self.root / 'axis-a.execution.json'
        receipt = json.loads(receipt_path.read_text()); receipt['notebook_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        receipt['executed_cells'] = 5; receipt_path.write_text(json.dumps(receipt))
        self.assert_invalid('every numbered section needs executable code')

    def test_no_curve_is_distinct_from_unperformed(self):
        self.doc['axes'][0]['curve'] = None
        axis = self.doc['axes'][1]
        axis['performed'] = False
        for name in ['notebook', 'execution', 'started_at', 'finished_at', 'curve']:
            axis[name] = None
        self.save(); _, items, _ = report.validate(self.sequence)
        self.assertEqual(report.status(items[0]), 'Tested · no curve produced')
        self.assertEqual(report.status(items[1]), 'Not performed')

    def test_render_preserves_exact_png_and_order(self):
        output = report.render(self.sequence, self.root / 'rendered')
        manifest = json.loads((output / 'render-manifest.json').read_text())
        self.assertEqual([a['id'] for a in manifest['axes']], self.doc['expected_axis_ids'])
        for axis in manifest['axes']:
            self.assertEqual((output / axis['curve']).read_bytes(), PNG)
        page = (output / 'index.html').read_text()
        self.assertIn('<details', page)
        self.assertIn('recorded test order', page)
        self.assertTrue((output / 'INVESTIGATION.md').is_file())
        self.assertEqual(page, (output / 'INVESTIGATION.html').read_text())
        notebook_html = (output / 'notebooks/01-axis-a.html').read_text()
        class Tags(HTMLParser):
            def __init__(self):
                super().__init__(); self.h2 = 0
            def handle_starttag(self, tag, attrs):
                self.h2 += tag == 'h2'
        tags = Tags(); tags.feed(notebook_html)
        self.assertEqual(tags.h2, 6)
        self.assertNotIn('&lt;h2', notebook_html)
        self.assertIn('<title>axis-a</title>', notebook_html)
        self.assertIn('Back to investigation', notebook_html)
        self.assertLess(page.index('<figure>'), page.index('Read notebook'))

    def test_table_and_list_form_sources(self):
        table = self.root / 'curve.csv'; table.write_text('level,mean\n1,0.5\n')
        self.doc['axes'][0]['tables'] = [{'path': table.name, 'role': 'Curve measurements',
                                       'sha256': hashlib.sha256(table.read_bytes()).hexdigest()}]
        notebook = self.root / 'axis-a.ipynb'; book = json.loads(notebook.read_text())
        for cell in book['cells']:
            cell['source'] = cell['source'].splitlines(keepends=True)
        notebook.write_text(json.dumps(book))
        receipt_path = self.root / 'axis-a.execution.json'; receipt = json.loads(receipt_path.read_text())
        receipt['notebook_sha256'] = hashlib.sha256(notebook.read_bytes()).hexdigest(); receipt_path.write_text(json.dumps(receipt))
        self.doc['axes'][0]['curve_caption'] = 'Unadjusted means; adjusted comparison above.'
        self.save(); output = report.render(self.sequence, self.root / 'rendered')
        page = (output / 'INVESTIGATION.html').read_text()
        self.assertIn('Unadjusted means; adjusted comparison above.', page)
        self.assertEqual((output / 'tables/01-axis-a-01.csv').read_bytes(), table.read_bytes())
        self.assertLess(page.index('Curve measurements'), page.index('Read notebook'))

    def test_table_hash_mismatch_rejected(self):
        table = self.root / 'curve.csv'; table.write_text('level,mean\n1,0.5\n')
        self.doc['axes'][0]['tables'] = [{'path': table.name, 'role': 'Curve', 'sha256': '0' * 64}]
        self.assert_invalid('table hash differs')

    def test_output_symlink_escape_rejected(self):
        output = self.root / 'rendered'; output.mkdir()
        outside = self.root / 'outside'; outside.mkdir()
        (output / 'notebooks').symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(report.ReportError, 'Generated path leaves'):
            report.render(self.sequence, output)


if __name__ == '__main__':
    unittest.main()
