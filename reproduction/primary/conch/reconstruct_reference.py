"""Rebuild the original deterministic NCT reference from exact public shards.

Reads only the row groups needed for the first 200 matching-label images in
each original shard. No CONCH inference. Original pixel-feature code is reused.
"""
from pathlib import Path
import hashlib
import io
import json
import sys
import zipfile

import pandas as pd
from PIL import Image
import pyarrow.parquet as pq
import requests

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'originals/scripts'))
import build_crc_candidate_table as original

REVISION = '97765ecb14bf11ce7bb8779a1097d187844a67cb'
OUT = ROOT / 'data/reference_reconstruction'
OUT.mkdir(exist_ok=True)


class RangeFile(io.RawIOBase):
    def __init__(self, url):
        super().__init__()
        self.url, self.position, self.ranges, self.receipts = url, 0, [], []
        response = requests.get(url, headers={'Range': 'bytes=-8'}, timeout=60)
        response.raise_for_status()
        assert response.status_code == 206
        self.size = int(response.headers['Content-Range'].split('/')[-1])
        self.ranges.append((self.size - 8, response.content))

    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.position
    def seek(self, offset, whence=0):
        self.position = offset if whence == 0 else self.position + offset if whence == 1 else self.size + offset
        return self.position

    def read(self, size=-1):
        if size < 0: size = self.size - self.position
        size = min(size, self.size - self.position)
        start = self.position
        self.position += size
        if not size: return b''
        for offset, raw in self.ranges:
            if offset <= start and start + size <= offset + len(raw):
                return raw[start-offset:start-offset+size]
        assert size < 20_000_000, f'Unexpected bulk read: {size}'
        response = requests.get(self.url, headers={'Range': f'bytes={start}-{start+size-1}'}, timeout=120)
        response.raise_for_status()
        assert response.status_code == 206 and len(response.content) == size
        raw = response.content
        self.ranges.append((start, raw))
        self.receipts.append({'start': start, 'length': size, 'sha256': hashlib.sha256(raw).hexdigest(),
                              'content_range': response.headers.get('Content-Range')})
        return raw


def main():
    import importlib.metadata
    for name, version in {'numpy':'2.4.6','Pillow':'12.1.1','pandas':'3.0.3'}.items():
        assert importlib.metadata.version(name) == version, f'Use requirements_reference.txt: {name}=={version}'
    all_rows, all_identities, downloads = [], [], []
    for label, shard in sorted(original.NCT_REFERENCE_SHARDS.items()):
        cls = original.LABEL_NAMES[label]
        csv_path = OUT / f'{cls}_features.csv'
        identity_path = OUT / f'{cls}_identities.json'
        receipt_path = OUT / f'{cls}_download.json'
        if csv_path.exists() and identity_path.exists() and receipt_path.exists() and (OUT/f'{cls}_images.zip').exists():
            rows = pd.read_csv(csv_path).to_dict(orient='records')
            identities = json.loads(identity_path.read_text())
            receipt = json.loads(receipt_path.read_text())
        else:
            url = original.HF_BASE.replace('/main/', f'/{REVISION}/') + shard
            stream = RangeFile(url)
            parquet = pq.ParquetFile(stream)
            rows, identities, source_offset = [], [], 0
            with zipfile.ZipFile(OUT / f'{cls}_images.zip', 'w', zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
                for group in range(parquet.metadata.num_row_groups):
                    labels = parquet.read_row_group(group, columns=['label']).column('label').to_pylist()
                    if label in labels:
                        batch = parquet.read_row_group(group, columns=['image', 'label']).to_pylist()
                        for local_index, example in enumerate(batch):
                            if int(example['label']) != label: continue
                            taken = len(rows)
                            image_record = example['image']
                            raw = image_record['bytes']
                            image = Image.open(io.BytesIO(raw))
                            features = original.image_features(image)
                            sample_id = f'nctref_{cls}_{taken:04d}'
                            rows.append({'source_split': 'NCT_CRC_HE_100K_reference',
                                         'source_record_index': taken, 'sample_id': sample_id,
                                         'image_path': '', 'label': label, 'label_name': cls,
                                         'reference_shard': shard, **features})
                            member = sample_id + Path(image_record.get('path') or '.tif').suffix
                            archive.writestr(member, raw)
                            identities.append({'sample_id': sample_id, 'shard': shard, 'revision': REVISION,
                                               'parquet_row_index': source_offset + local_index,
                                               'original_image_path': image_record.get('path'),
                                               'archive': f'{cls}_images.zip', 'member': member,
                                               'encoded_sha256': hashlib.sha256(raw).hexdigest(),
                                               'decoded_image_md5': features['image_md5']})
                            if len(rows) == 200: break
                    source_offset += len(labels)
                    if len(rows) == 200: break
            assert len(rows) == 200
            receipt = {'url': url, 'shard_size': stream.size, 'rows_selected': len(rows),
                       'total_range_bytes': sum(x['length'] for x in stream.receipts) + 8,
                       'requests': stream.receipts}
            pd.DataFrame(rows).to_csv(csv_path, index=False)
            identity_path.write_text(json.dumps(identities, indent=2))
            receipt_path.write_text(json.dumps(receipt, indent=2))
        all_rows.extend(rows); all_identities.extend(identities); downloads.append(receipt)
        print(json.dumps({'class': cls, 'selected': len(rows), 'range_bytes': receipt['total_range_bytes']}), flush=True)
    from replay_reference_pixels import replay_pixels
    (OUT / 'identities.json').write_text(json.dumps(all_identities, indent=2))
    reference = replay_pixels()
    assert len(reference) == 1800 and reference.sample_id.is_unique
    reference.to_csv(ROOT / 'data/nct_reference_features.reconstructed.csv', index=False)
    (OUT / 'download_receipts.json').write_text(json.dumps(downloads, indent=2))
    print('Saved reconstructed reference: 1,800 rows', flush=True)


if __name__ == '__main__': main()
