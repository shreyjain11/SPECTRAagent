"""Expand the small offline input package without changing any original file bytes.

The zip is content-addressed: original paths are only in the checked manifest.
Bulk structures, alignments, model weights and installed model source are absent.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import os
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parent

def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

def ensure_assets(root=None, verify_only=False):
    root = (Path(root) if root is not None else ROOT).resolve()
    manifest = json.loads((root / 'artifact_manifest.json').read_text())
    missing = []
    for item in manifest['files']:
        relative = PurePosixPath(item['path'])
        if relative.is_absolute() or any(part in ('', '.', '..') for part in relative.parts):
            raise ValueError('Unsafe artifact path: ' + item['path'])
        path = root.joinpath(*relative.parts)
        if not path.resolve().is_relative_to(root):
            raise ValueError('Artifact resolves outside package: ' + item['path'])
        if path.exists():
            if not path.is_file() or path.stat().st_size != item['bytes'] or sha256(path) != item['sha256']:
                raise ValueError('Existing original artifact changed; refusing overwrite: ' + str(path))
        else:
            missing.append((path, item))
    if verify_only and missing:
        raise FileNotFoundError('Artifacts are not expanded; run python bootstrap.py first')
    if missing:
        archive = root / manifest['archive']
        if archive.stat().st_size != manifest['archive_bytes'] or sha256(archive) != manifest['archive_sha256']:
            raise ValueError('Offline artifact archive hash mismatch')
        expected_objects = {'sha256/' + item['sha256'] for item in manifest['files']}
        with zipfile.ZipFile(archive) as bundle:
            if set(bundle.namelist()) != expected_objects or len(bundle.infolist()) != len(expected_objects):
                raise ValueError('Offline artifact inventory differs from manifest')
            for path, item in missing:
                data = bundle.read('sha256/' + item['sha256'])
                if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
                    raise ValueError('Original artifact object hash mismatch: ' + item['path'])
                path.parent.mkdir(parents=True, exist_ok=True)
                # Publish only completed bytes. Concurrent notebooks may bootstrap the
                # same package; none should observe another writer's partial file.
                temporary = None
                try:
                    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as output:
                        temporary = Path(output.name)
                        output.write(data)
                    try:
                        os.link(temporary, path)
                    except FileExistsError:
                        if sha256(path) != item['sha256']:
                            raise ValueError('Concurrent artifact change: ' + str(path))
                finally:
                    if temporary is not None:
                        temporary.unlink(missing_ok=True)
    return {'verified_files': len(manifest['files']), 'restored_files': len(missing),
            'archive_sha256': manifest['archive_sha256'], 'network_used': False}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify-only', action='store_true')
    args = parser.parse_args()
    print(json.dumps(ensure_assets(verify_only=args.verify_only), indent=2))
