"""Download and verify the public data used by the retained notebook calculations."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tempfile
import time
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parent


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def data_directory():
    return Path(os.environ.get('SPECTRA_DATA_DIR', ROOT / '.data')).expanduser().resolve()


@contextlib.contextmanager
def lock(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Notebook kernels preparing the same model share one download/extraction.
    import fcntl
    with path.open('a') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def download(spec, destination):
    if destination.is_file() and digest(destination) == spec['sha256']:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=destination.name + '.', suffix='.part', dir=destination.parent)
    checksum = hashlib.sha256()
    count = 0
    last_notice = 0
    try:
        request = urllib.request.Request(spec['url'], headers={'User-Agent': 'SPECTRA-reproduction/1'})
        with os.fdopen(descriptor, 'wb') as target, urllib.request.urlopen(request, timeout=60) as response:
            if 'text/html' in response.headers.get('Content-Type', ''):
                raise ValueError('The data URL returned HTML instead of an archive.')
            while block := response.read(4 * 1024 * 1024):
                target.write(block)
                checksum.update(block)
                count += len(block)
                if count - last_notice >= 100 * 1024 * 1024:
                    print(f"Downloading {spec['model']}: {count // (1024 * 1024)} MiB", file=sys.stderr, flush=True)
                    last_notice = count
        if count != spec['bytes'] or checksum.hexdigest() != spec['sha256']:
            raise ValueError(f"Archive size or SHA-256 mismatch: {spec['model']}")
        os.replace(temporary, destination)
    finally:
        Path(temporary).unlink(missing_ok=True)


def extract(archive, destination):
    with zipfile.ZipFile(archive) as source:
        for member in source.infolist():
            path = PurePosixPath(member.filename)
            if path.is_absolute() or '..' in path.parts or '\\' in member.filename:
                raise ValueError(f'Unsafe archive path: {member.filename}')
            if stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError(f'Archive symlink is not allowed: {member.filename}')
        source.extractall(destination)


def verify_inputs(directory):
    manifest = read(directory / 'PUBLIC_INPUTS.json')
    for entry in manifest['files']:
        path = directory / entry['path']
        if not path.is_file() or path.stat().st_size != entry['bytes'] or digest(path) != entry['sha256']:
            raise ValueError(f"Input missing or changed: {entry['path']}")
    return manifest


def install_code(model, directory):
    manifest = read(directory / 'PUBLIC_INPUTS.json')
    hashes = {entry['path']: {'sha256': entry['sha256'], 'bytes': entry['bytes']} for entry in manifest['files']}
    code = read(ROOT / 'code' / f'{model}.json')
    for entry in code:
        source = ROOT / entry['path']
        if digest(source) != entry['sha256']:
            raise ValueError(f"Published code changed: {entry['path']}")
        relative = source.relative_to(ROOT / 'materials' / model)
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_file() or digest(target) != entry['sha256']:
            shutil.copyfile(source, target)
        hashes[relative.as_posix()] = {'sha256': entry['sha256'], 'bytes': source.stat().st_size}
    descriptor, temporary = tempfile.mkstemp(prefix='.public-hashes.', dir=directory)
    try:
        with os.fdopen(descriptor, 'w') as stream:
            stream.write(json.dumps(hashes, indent=2) + '\n')
        os.replace(temporary, directory / 'PUBLIC_FILE_HASHES.json')
    finally:
        Path(temporary).unlink(missing_ok=True)
    return directory


def prepare_model(model, archive=None, verify=False):
    catalog = read(ROOT / 'data.json')
    spec = next((entry for entry in catalog['archives'] if entry['model'] == model), None)
    if spec is None:
        raise ValueError(f'Unknown model: {model}')
    cache = data_directory()
    destination = cache / catalog['release'] / model
    with lock(cache / (model + '.lock')):
        marker = destination / '.prepared.json'
        existing = read(marker) if marker.is_file() else {}
        if existing.get('archive_sha256') != spec['sha256']:
            if destination.exists():
                raise ValueError(f'An older or incomplete cache exists: {destination}. Choose another SPECTRA_DATA_DIR.')
            if archive is None:
                archive = cache / 'archives' / spec['file']
                download(spec, archive)
            else:
                archive = Path(archive).expanduser().resolve()
                if not archive.is_file() or archive.stat().st_size != spec['bytes'] or digest(archive) != spec['sha256']:
                    raise ValueError(f'Local archive does not match the published checksum: {archive}')
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = Path(tempfile.mkdtemp(prefix=model + '.', dir=destination.parent))
            try:
                extract(archive, temporary)
                manifest = verify_inputs(temporary)
                (temporary / '.prepared.json').write_text(json.dumps({
                    'archive_sha256': spec['sha256'], 'input_files': len(manifest['files']),
                    'verified_at_unix': time.time(),
                }, indent=2) + '\n')
                temporary.rename(destination)
            finally:
                if temporary.exists():
                    shutil.rmtree(temporary)
        elif verify:
            verify_inputs(destination)
        return install_code(model, destination)


def prepare_notebook(analysis_id):
    record_path = ROOT / 'analyses' / (analysis_id + '.json')
    if not record_path.resolve().is_relative_to(ROOT / 'analyses'):
        raise ValueError('Invalid analysis identifier.')
    record = read(record_path)
    model = Path(record['dataset_split']['input_inventory']).stem
    directory = prepare_model(model)
    relative = Path(record['implementation']['notebook']).relative_to(Path('materials') / model)
    notebook_directory = directory / relative.parent
    notebook_directory.mkdir(parents=True, exist_ok=True)
    for path in [directory, notebook_directory, directory / 'upstream_checks']:
        sys.path.insert(0, str(path))
    os.chdir(notebook_directory)
    return directory


def input_hashes(directory):
    return read(Path(directory) / 'PUBLIC_FILE_HASHES.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--model', choices=['state', 'esmfold2', 'conch', 'alphamissense'])
    selection.add_argument('--all', action='store_true')
    parser.add_argument('--archive', type=Path, help='Optional local copy of the same public archive; SHA-256 is checked.')
    parser.add_argument('--verify', action='store_true', help='Recheck every cached input file.')
    args = parser.parse_args()
    if args.all and args.archive:
        parser.error('--archive requires --model')
    models = [args.model] if args.model else ['state', 'esmfold2', 'conch', 'alphamissense']
    for model in models:
        print(prepare_model(model, args.archive, args.verify))


if __name__ == '__main__':
    main()
