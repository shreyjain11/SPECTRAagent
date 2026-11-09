"""Acquire exact pinned HF files, verify LFS digests, and retain a receipt."""
import argparse
import hashlib
import json
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    from huggingface_hub import HfApi, hf_hub_download
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    request = json.loads(args.request.read_text())
    api = HfApi()
    info = api.repo_info(request['repo_id'], repo_type=request['repo_type'],
                         revision=request['revision'], files_metadata=True)
    assert info.sha == request['revision']
    members = {r.rfilename: r for r in info.siblings}
    rows = []
    for filename in request['filenames']:
        metadata = members[filename]
        lfs = metadata.lfs
        expected = lfs.sha256 if hasattr(lfs, 'sha256') else (lfs or {}).get('sha256')
        if not expected:
            raise RuntimeError('Pinned large file lacks an upstream SHA256: ' + filename)
        path = Path(hf_hub_download(request['repo_id'], filename,
                    repo_type=request['repo_type'], revision=request['revision'],
                    local_dir=str(args.destination)))
        actual = sha256(path)
        assert actual == expected, filename
        rows.append({'filename': filename, 'path': str(path.resolve()),
                     'bytes': path.stat().st_size, 'sha256': actual})
    args.receipt.write_text(json.dumps({**request, 'files': rows}, indent=2))


if __name__ == '__main__':
    main()
