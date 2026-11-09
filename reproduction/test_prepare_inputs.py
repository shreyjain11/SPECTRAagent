"""Integrity and extraction checks for the public data installer."""
import hashlib
import io
import json
from pathlib import Path
import stat
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import prepare_inputs as inputs


class Response(io.BytesIO):
    def __init__(self, data, content_type='application/zip'):
        super().__init__(data)
        self.headers = {'Content-Type': content_type}


class PublicInputTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)

    def spec(self, data):
        return {'model': 'example', 'url': 'https://example.org/data.zip',
                'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

    def test_download_checks_bytes_and_reuses_verified_archive(self):
        data = b'public example data'
        destination = self.directory / 'data.zip'
        with patch.object(inputs.urllib.request, 'urlopen', return_value=Response(data)) as call:
            inputs.download(self.spec(data), destination)
            inputs.download(self.spec(data), destination)
            self.assertEqual(call.call_count, 1)
        self.assertEqual(destination.read_bytes(), data)

    def test_download_refuses_wrong_hash_and_removes_partial_file(self):
        with patch.object(inputs.urllib.request, 'urlopen', return_value=Response(b'wrong bytes')):
            with self.assertRaisesRegex(ValueError, 'mismatch'):
                inputs.download(self.spec(b'right bytes'), self.directory / 'data.zip')
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_download_refuses_html(self):
        with patch.object(inputs.urllib.request, 'urlopen', return_value=Response(b'<html>login</html>', 'text/html')):
            with self.assertRaisesRegex(ValueError, 'HTML'):
                inputs.download(self.spec(b'archive'), self.directory / 'data.zip')
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_extraction_refuses_parent_traversal(self):
        archive = self.directory / 'bad.zip'
        with zipfile.ZipFile(archive, 'w') as stream:
            stream.writestr('../outside.txt', b'bad')
        with self.assertRaisesRegex(ValueError, 'Unsafe'):
            inputs.extract(archive, self.directory / 'output')
        self.assertFalse((self.directory / 'outside.txt').exists())

    def test_extraction_refuses_symlinks(self):
        archive = self.directory / 'bad.zip'
        info = zipfile.ZipInfo('link')
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with zipfile.ZipFile(archive, 'w') as stream:
            stream.writestr(info, '/outside')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            inputs.extract(archive, self.directory / 'output')

    def test_file_verification_detects_missing_and_changed_input(self):
        path = self.directory / 'measurements.csv'
        data = b'sample,score\na,0.5\n'
        manifest = {'files': [{'path': path.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}]}
        (self.directory / 'PUBLIC_INPUTS.json').write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'missing or changed'):
            inputs.verify_inputs(self.directory)
        path.write_bytes(data)
        self.assertEqual(inputs.verify_inputs(self.directory), manifest)
        path.write_bytes(data.replace(b'0.5', b'0.6'))
        with self.assertRaisesRegex(ValueError, 'missing or changed'):
            inputs.verify_inputs(self.directory)


if __name__ == '__main__':
    unittest.main()
