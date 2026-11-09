"""Recompute all reference features from the 1,800 saved original shard images."""
from pathlib import Path
import io
import json
import sys
import zipfile

import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'originals/scripts'))
import build_crc_candidate_table as original


def replay_pixels():
    folder = ROOT / 'data/reference_reconstruction'
    identities = json.loads((folder/'identities.json').read_text())
    rows = []
    for label, shard in sorted(original.NCT_REFERENCE_SHARDS.items()):
        cls = original.LABEL_NAMES[label]
        with zipfile.ZipFile(folder/f'{cls}_images.zip') as archive:
            for identity in [r for r in identities if r['shard']==shard]:
                image = Image.open(io.BytesIO(archive.read(identity['member'])))
                features = original.image_features(image)
                assert features['image_md5'] == identity['decoded_image_md5']
                rows.append({'source_split':'NCT_CRC_HE_100K_reference',
                             'source_record_index':int(identity['sample_id'].rsplit('_',1)[1]),
                             'sample_id':identity['sample_id'],'image_path':'','label':label,
                             'label_name':cls,'reference_shard':shard,**features})
    return pd.DataFrame(rows)


if __name__ == '__main__':
    destination = Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'data/nct_reference_features.numericmatched.csv'
    frame = replay_pixels()
    frame.to_csv(destination,index=False)
    print(f'Recomputed {len(frame)} rows from exact cached images: {destination}')
