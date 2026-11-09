"""Read only original H5AD observations through pinned HTTP range requests.

Full H5AD LFS hashes identify the immutable source object; they are NOT claimed
as locally verified full-file checksums. Extracted observation tables are hashed.
"""
import argparse,json
from pathlib import Path
import fsspec,h5py
import numpy as np
import pandas as pd
from common import sha,dump,save_receipt

def decode(a):
    if a.dtype.kind in ['O','S','U']:return np.array([x.decode() if isinstance(x,bytes) else str(x) for x in a],dtype=object)
    return a
def field(group,name):
    x=group[name]
    if isinstance(x,h5py.Dataset):return decode(x[:])
    cats=decode(x['categories'][:]);codes=x['codes'][:];return np.array([cats[c] if c>=0 else None for c in codes],dtype=object)
def run(root):
    out=root/'computed/replogle';out.mkdir(parents=True,exist_ok=True);inp=root/'inputs/observation_extracts';inp.mkdir(parents=True,exist_ok=True)
    spec=json.loads((root/'methods/sources.json').read_text())['remote_observations'];parts=[];evidence=[]
    fs=fsspec.filesystem('http')
    for x in spec:
        context=x['path'].split('/')[2];print('OBSERVATIONS',context,flush=True)
        with fs.open(x['url'],'rb',block_size=262144,cache_type='blockcache',size=x['bytes']) as f:
            with h5py.File(f,'r') as h:
                d=pd.DataFrame({k:field(h['obs'],k) for k in ['gene','cell_line','gem_group','pert_cell_barcode','ctrl_cell_barcode']})
        if d.cell_line.nunique()!=1:raise ValueError('Unexpected context mixing')
        p=inp/f'{context}.parquet';d.to_parquet(p,index=False)
        counts=d.groupby('gene',observed=True).agg(n_treated=('pert_cell_barcode','nunique'),n_control=('ctrl_cell_barcode','nunique'),n_rows=('gene','size')).reset_index().rename(columns={'gene':'perturbation'})
        counts['context']=context;parts.append(counts)
        evidence.append(dict(source=x,access='Pinned immutable H5AD; HTTP range extraction of obs only',full_source_sha256_verified=False,extracted_path=str(p.relative_to(root)),extracted_sha256=sha(p),extracted_rows=len(d)))
    result=pd.concat(parts,ignore_index=True);result.to_csv(out/'cell_counts.csv',index=False);dump(out/'observation_source_receipt.json',evidence)
    save_receipt(root,'replogle_observations',[inp/f'{x["path"].split("/")[2]}.parquet' for x in spec],[out/'cell_counts.csv',out/'observation_source_receipt.json'],dict(contexts=len(parts),unique_condition_rows=len(result),count_definition='nunique pert_cell_barcode and nunique ctrl_cell_barcode within original gene/context'),['Raw H5AD arrays are not downloaded; input-side observation extraction is pinned to original release objects and retains extracted-table checksums.'])
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();run(a.root.resolve())
