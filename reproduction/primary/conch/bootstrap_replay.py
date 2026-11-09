"""Materialize the exact small replay tables bundled with this package.

No network, image cache, model checkpoint or external workspace is needed.
Compressed and expanded SHA256 values are checked before a file is used.
"""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def materialize():
    records = json.loads((ROOT / 'PAYLOAD_MANIFEST.json').read_text())
    for record in records:
        destination = (ROOT / record['destination']).resolve()
        archive = (ROOT / record['archive']).resolve()
        if not destination.is_relative_to(ROOT / 'data') or not archive.is_relative_to(ROOT / 'payload'):
            raise ValueError('Payload manifest contains a path outside its package.')
        encoded = archive.read_bytes()
        assert hashlib.sha256(encoded).hexdigest() == record['archive_sha256'], str(archive)
        if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() == record['expanded_sha256']:
            continue
        raw = gzip.decompress(encoded)
        assert len(raw) == record['expanded_bytes']
        assert hashlib.sha256(raw).hexdigest() == record['expanded_sha256'], str(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + '.tmp')
        temporary.write_bytes(raw)
        temporary.replace(destination)
    return records


if __name__ == '__main__':
    records = materialize()
    print(json.dumps({'materialized': len(records), 'network_used': False,
                      'expanded_bytes': sum(r['expanded_bytes'] for r in records)}, indent=2))
