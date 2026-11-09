"""Acquire documented original inputs; verify original sizes and SHA-256.

Listing is the default. Pass --fetch and optional --path to download files.
No analysis outcome enters source selection or validation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import urllib.request
import urllib.parse
import zipfile

BASE = Path(__file__).resolve().parent


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def checked_path(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Input path escapes destination')
    return path


def matches(path, entry):
    return (path.is_file() and path.stat().st_size == entry['bytes']
            and sha256(path) == entry['sha256'])


def entries(manifest):
    unique = {}
    for entry in manifest['inputs']:
        previous = unique.get(entry['path'])
        if previous and any(previous[k] != entry[k] for k in ['bytes', 'sha256']):
            raise ValueError('Conflicting original input identities: ' + entry['path'])
        unique.setdefault(entry['path'], entry)
    return list(unique.values())


def fetch(entry, root):
    path = checked_path(root, entry['path'])
    if matches(path, entry):
        return {'path': entry['path'], 'status': 'verified_existing'}
    if path.exists():
        raise ValueError('Existing input differs from original; will not overwrite: ' + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.download-part')
    parts = urllib.parse.urlsplit(entry['url'])
    url = urllib.parse.urlunsplit(parts._replace(path=urllib.parse.quote(parts.path, safe='/%')))
    request = urllib.request.Request(url, headers={'User-Agent': 'STATE-historical-reconstruction/1.0'})
    h = hashlib.sha256(); count = 0
    try:
        with urllib.request.urlopen(request, timeout=90) as response, temporary.open('wb') as f:
            if response.status != 200:
                raise ValueError('Unexpected download status')
            for block in iter(lambda: response.read(8 * 1024 * 1024), b''):
                count += len(block)
                if count > entry['bytes']:
                    raise ValueError('Download exceeds original byte count')
                h.update(block); f.write(block)
        if count != entry['bytes'] or h.hexdigest() != entry['sha256']:
            raise ValueError('Download does not match original input: ' + entry['path'])
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return {'path': entry['path'], 'status': 'downloaded_verified', 'bytes': count, 'sha256': h.hexdigest()}


def extract_cmp(root, manifest):
    entry = manifest['cmp_member']
    archive_entry = next(e for e in entries(manifest) if e['path'].endswith('cmp_rnaseq_all_20220624.zip'))
    archive_path = checked_path(root, archive_entry['path'])
    if not matches(archive_path, archive_entry):
        raise ValueError('CMP archive must match its original checksum before extraction')
    output = checked_path(root, entry['path'])
    if matches(output, entry): return {'path': entry['path'], 'status': 'verified_existing'}
    if output.exists(): raise ValueError('Existing CMP table differs from original')
    temporary = output.with_name(output.name + '.extract-part')
    try:
        with zipfile.ZipFile(archive_path) as archive:
            member = archive.getinfo(entry['archive_member'])
            if member.file_size != entry['bytes']: raise ValueError('CMP member size mismatch')
            with archive.open(member) as source, temporary.open('wb') as target:
                for block in iter(lambda: source.read(8 * 1024 * 1024), b''): target.write(block)
        if not matches(temporary, entry): raise ValueError('CMP table checksum mismatch')
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    return {'path': entry['path'], 'status': 'extracted_verified', 'sha256': entry['sha256']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fetch', action='store_true')
    parser.add_argument('--path', action='append', default=[], help='Exact manifest path; repeat to select a subset')
    parser.add_argument('--output', type=Path, default=BASE.parent / 'inputs')
    args = parser.parse_args()
    manifest = json.loads((BASE / 'sources.json').read_text())
    selected = entries(manifest)
    if args.path:
        missing = set(args.path) - {e['path'] for e in selected}
        if missing: parser.error('Unknown manifest paths: ' + ', '.join(sorted(missing)))
        selected = [e for e in selected if e['path'] in args.path]
    print(json.dumps({'files': len(selected), 'bytes': sum(e['bytes'] for e in selected),
                      'mode': 'fetch' if args.fetch else 'list',
                      'paths': [e['path'] for e in selected]}, indent=2), flush=True)
    if not args.fetch: return
    receipts = []
    for entry in selected:
        receipt = fetch(entry, args.output)
        receipts.append(receipt); print(json.dumps(receipt), flush=True)
        if entry['path'].endswith('cmp_rnaseq_all_20220624.zip'):
            receipt = extract_cmp(args.output, manifest)
            receipts.append(receipt); print(json.dumps(receipt), flush=True)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'last_download_receipt.json').write_text(json.dumps(receipts, indent=2) + '\n')


if __name__ == '__main__':
    main()
