"""Restore exact primary-reproduction inputs; no inference or scientific processing.

Local versioned payloads are expanded automatically. The one external AM search
output is fetched only if absent, from the manifest's immutable release asset.
Every source and expanded member is checked against its recorded SHA256.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,tarfile,tempfile,urllib.request
ROOT=Path(__file__).resolve().parent

def digest(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for chunk in iter(lambda:f.read(8*1024*1024),b''):h.update(chunk)
 return h.hexdigest()

def check(path,item):
 path=Path(path)
 return path.is_file() and path.stat().st_size==item['bytes'] and digest(path)==item['sha256']

def safe_path(relative):
 target=(ROOT/relative).resolve()
 if ROOT not in target.parents:raise ValueError('Unsafe payload path: '+relative)
 return target

def ensure_inputs(profile='default',allow_download=True,asset_dir=None):
 manifest=json.loads((ROOT/'payload_manifest.json').read_text());records=[]
 if profile=='all':assets=manifest['assets']
 else:assets=[a for a in manifest['assets'] if profile in a['profiles'] or 'default' in a['profiles']]
 if not assets:raise ValueError('Unknown input profile: '+profile)
 for asset in assets:
  members=asset['members'];missing=[m for m in members if not check(safe_path(m['path']),m)]
  if not missing:
   records.append({'asset':asset['name'],'members':len(members),'source':'verified_existing_inputs'});continue
  for member in missing:
   target=safe_path(member['path'])
   if target.exists():raise ValueError('Existing historical input differs; preserve and inspect it: '+str(target))
  source=ROOT/asset['path'] if asset.get('path') else Path(asset_dir)/asset['name'] if asset_dir else ROOT/'downloads'/asset['name']
  if not source.is_file():
   if not asset.get('url'):raise FileNotFoundError('Missing versioned Git payload: '+str(source))
   if not allow_download:raise FileNotFoundError('Exact external input required: '+asset['url']+'; run without --offline or supply --asset-dir.')
   if asset.get('publication_status')!='verified_public':raise RuntimeError('Release asset publication has not yet been verified: '+asset['url'])
   source.parent.mkdir(parents=True,exist_ok=True)
   part=source.with_suffix(source.suffix+'.partial')
   request=urllib.request.Request(asset['url'],headers={'User-Agent':'SPECTRA-primary-reproduction'})
   with urllib.request.urlopen(request,timeout=120) as response,part.open('wb') as out:shutil.copyfileobj(response,out,8*1024*1024)
   if not check(part,asset):part.unlink();raise ValueError('Downloaded source hash mismatch: '+asset['name'])
   part.replace(source)
  if not check(source,asset):raise ValueError('Versioned payload hash mismatch: '+str(source))
  if asset['kind']=='file':
   assert len(members)==1
   target=safe_path(members[0]['path']);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
  else:
   wanted={m['path']:m for m in members};seen=set()
   with tarfile.open(source,'r:gz') as archive:
    for member in archive:
     if member.name not in wanted or not member.isfile() or member.name in seen:raise ValueError('Unexpected archive member: '+member.name)
     seen.add(member.name);item=wanted[member.name];target=safe_path(member.name)
     if check(target,item):continue
     target.parent.mkdir(parents=True,exist_ok=True);temporary=target.with_suffix(target.suffix+'.partial')
     with archive.extractfile(member) as inp,temporary.open('wb') as out:shutil.copyfileobj(inp,out)
     if not check(temporary,item):temporary.unlink();raise ValueError('Expanded input hash mismatch: '+member.name)
     temporary.replace(target);target.chmod(member.mode & 0o777)
   if seen!=set(wanted):raise ValueError('Archive member inventory mismatch: '+asset['name'])
  if not all(check(safe_path(m['path']),m) for m in members):raise ValueError('Restored-input verification failed: '+asset['name'])
  records.append({'asset':asset['name'],'members':len(members),'source':'manifest_verified_payload'})
 return {'profile':profile,'verified_files':sum(r['members'] for r in records),'assets':records,'new_model_inference':False}

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--profile',default='all');parser.add_argument('--offline',action='store_true');parser.add_argument('--asset-dir',type=Path)
 args=parser.parse_args();print(json.dumps(ensure_inputs(args.profile,not args.offline,args.asset_dir),indent=2))
