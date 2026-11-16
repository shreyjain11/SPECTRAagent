"""Restore the exact public retained inputs for the partial correction runner."""
from pathlib import Path
import json,gzip,hashlib,argparse
p=argparse.ArgumentParser();p.add_argument('--work',type=Path,required=True);args=p.parse_args()
base=Path(__file__).resolve().parent;reproduction=base.parents[2]
for x in json.load(open(base/'packaged_input_manifest.json'))['inputs']:
 compressed=(reproduction/x['path']).read_bytes();assert hashlib.sha256(compressed).hexdigest()==x['sha256'];data=gzip.decompress(compressed);assert hashlib.sha256(data).hexdigest()==x['uncompressed_sha256']
 target=args.work/x['work_relative_path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
print('Restored exact hash-verified inputs; no authentication or inference is needed.')
