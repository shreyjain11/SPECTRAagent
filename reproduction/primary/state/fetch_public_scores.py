"""Reacquire the exact58 public STATE score/metadata inputs; no inference."""
from pathlib import Path
import json,shutil,urllib.request,urllib.parse
from state_inputs import ROOT,check,safe_path

def fetch():
 records=[]
 for item in json.loads((ROOT/'download_manifest.json').read_text())['files']:
  target=safe_path(item['local'])
  if target.exists():
   if not check(target,item):raise ValueError('Existing input differs: '+str(target))
  else:
   target.parent.mkdir(parents=True,exist_ok=True);part=target.with_suffix(target.suffix+'.partial')
   url=urllib.parse.urlsplit(item['pinned_download_url'])
   encoded=urllib.parse.urlunsplit(url._replace(path=urllib.parse.quote(url.path,safe='/%')))
   request=urllib.request.Request(encoded,headers={'User-Agent':'SPECTRA-primary-reproduction'})
   with urllib.request.urlopen(request,timeout=120) as response,part.open('wb') as out:shutil.copyfileobj(response,out)
   if not check(part,item):part.unlink();raise ValueError('Pinned public file hash differs: '+item['path'])
   part.replace(target)
  # The preserved original loader requests the local default revision. Bind
  # that reference to the exact downloaded snapshot rather than current main.
  parts=target.parts;split=parts.index('snapshots')
  ref=Path(*parts[:split])/'refs/main';ref.parent.mkdir(parents=True,exist_ok=True)
  if ref.exists() and ref.read_text().strip()!=item['revision']:raise ValueError('Unexpected cached repository revision: '+str(ref))
  if not ref.exists():ref.write_text(item['revision'])
  records.append({'path':item['local'],'sha256':item['sha256']})
 return records
if __name__=='__main__':print(json.dumps(fetch(),indent=2))
