"""Acquire immutable released inputs on the execution host; never fetch model weights.

Only checksum-verified identical objects may be reused from another local package.
The original audit supplied hashes for metadata/A8/A10; other hashes are obtained
from the same historical model commit's immutable Hugging Face LFS inventory.
"""
import argparse, concurrent.futures, hashlib, json, os, time, urllib.request
from pathlib import Path
from urllib.parse import quote

CTX = ['k562', 'jurkat', 'hepg2', 'rpe1']
TCTX = ['C32', 'HOP62', 'HepG2-C3A', 'Hs 766T', 'PANC-1']
REV = {'ST-SE-Replogle':'e324967ff4cea5ec199e29bcbb5c1f00e5b9d69c',
       'ST-HVG-Replogle':'bb6a9562cbbf1fd152df14cc53b4cc7517c77175',
       'ST-SE-Tahoe':'03b1971d7cc93a7535fd2e957c6948dba267378b',
       'ST-HVG-Tahoe':'ca6b751972493f8448e3256d1340ae70ad43e1e7'}
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()
def getjson(u):
    with urllib.request.urlopen(u,timeout=120) as f:return json.load(f)
def manifest(root):
    records=[]; remote_obs=[]
    original=json.loads((root/'originals/supporting/audit/manifests/provenance.json').read_text())
    for x in original['resources']:
        if x['id'] in ['state-split-tahoe','depmap-24q4-expression','depmap-24q4-model-map','hpa-cellline-rna']:
            url=x['source_url'].replace('github.com/ArcInstitute/state/blob/','raw.githubusercontent.com/ArcInstitute/state/')
            records.append(dict(path='metadata/'+Path(x['local_path']).name,url=url,sha256=x['sha256'],bytes=x['bytes'],evidence='Original audit provenance'))
    for name,rev in REV.items():
        paths=[f'zeroshot/{c}/eval_best.ckpt' for c in CTX] if 'Replogle' in name else (['fewshot/state_generalization_X_state/eval_best.ckpt','zeroshot/state_generalization_zeroshot_X_state/eval_best.ckpt'] if name=='ST-SE-Tahoe' else ['zeroshot/state_generalization_zeroshot_X_hvg/eval_best.ckpt'])
        for base in paths:
            items=getjson(f'https://huggingface.co/api/models/arcinstitute/{name}/tree/{rev}/{base}?recursive=true')
            for f in items:
                p=f['path']; url=f'https://huggingface.co/arcinstitute/{name}/resolve/{rev}/'+quote(p)
                if p.endswith('adata_real.h5ad') and name=='ST-SE-Replogle':
                    remote_obs.append(dict(path=f'{name}/{p}',url=url,bytes=f['size'],sha256=f['lfs']['oid'],evidence='Pinned original release; observation-only range extraction'))
                wanted=(p.endswith('_results.csv') and not p.endswith('_agg_results.csv')) or ('Replogle' in name and p.endswith(('_real_de.csv','_pred_de.csv'))) or (name=='ST-HVG-Tahoe' and p.endswith('_real_de.csv'))
                if not wanted:continue
                records.append(dict(path=f'{name}/{p}',url=url,bytes=f['size'],sha256=f['lfs']['oid'],evidence='HF LFS object at original audit revision',revision=rev))
    # The original condition-count provenance names State-Tahoe-Filtered but
    # describes the public Tahoe obs_metadata parquet. Preserve this ambiguity.
    records.append(dict(path='metadata/tahoe_obs_metadata.parquet',url='https://huggingface.co/datasets/tahoebio/Tahoe-100M/resolve/2dc57900b7981cfcf5e211527169a0b006546a95/metadata/obs_metadata.parquet',bytes=2293981573,sha256='e51b24f3666f5f433c59ff01dd6fa33934627091455e89d929f2c1ddc87401fe',evidence='Same public metadata bytes verified by original Codex r1; reconstructed source resolution for r2 count/QC controls'))
    out=dict(inputs=records,remote_observations=remote_obs,created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
    (root/'methods/sources.json').write_text(json.dumps(out,indent=2)+'\n')
    return out
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--reuse',type=Path);ap.add_argument('--manifest-only',action='store_true');ap.add_argument('--refresh-manifest',action='store_true');a=ap.parse_args();r=a.root.resolve()
    p=r/'methods/sources.json';m=json.loads(p.read_text()) if p.exists() and not a.refresh_manifest else manifest(r)
    if a.manifest_only:return
    reuse={}
    if a.reuse:
        for x in json.loads((a.reuse/'methods/sources.json').read_text())['inputs']:reuse[x['sha256']]=a.reuse/'inputs'/x['path']
    def one(x):
        p=r/'inputs'/x['path'];p.parent.mkdir(parents=True,exist_ok=True)
        if p.exists() and p.stat().st_size==x['bytes'] and sha(p)==x['sha256']:return {**x,'verified':True,'route':'existing'}
        q=reuse.get(x['sha256'])
        if q and q.exists() and q.stat().st_size==x['bytes'] and sha(q)==x['sha256']:
            p.symlink_to(q.resolve());print('REUSE',x['path'],flush=True);return {**x,'verified':True,'route':'identical_sha256_symlink'}
        tmp=p.with_name(p.name+'.part')
        for attempt in range(4):
            try:
                with urllib.request.urlopen(x['url'],timeout=180) as src,tmp.open('wb') as dst:
                    for b in iter(lambda:src.read(8*1024*1024),b''):dst.write(b)
                assert tmp.stat().st_size==x['bytes'],(tmp.stat().st_size,x['bytes'])
                assert sha(tmp)==x['sha256'],'Source checksum mismatch'
                os.replace(tmp,p);print('VERIFIED',x['path'],x['bytes'],flush=True)
                return {**x,'verified':True,'route':'public_download'}
            except Exception:
                if attempt==3:raise
                time.sleep(2*(attempt+1))
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:done=list(pool.map(one,m['inputs']))
    (r/'inputs/DOWNLOAD_RECEIPT.json').write_text(json.dumps(dict(source_manifest_sha256=sha(r/'methods/sources.json'),inputs=done),indent=2)+'\n')
if __name__=='__main__':main()
