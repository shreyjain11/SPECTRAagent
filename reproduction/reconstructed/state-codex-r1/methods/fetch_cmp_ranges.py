"""Fetch the slow public CMP archive in bounded byte ranges, then verify it.

This is a transport optimization only. The original complete-file checksum is
required before the archive is installed or extracted.
"""
import argparse
import concurrent.futures
import json
import os
from pathlib import Path
import time
import urllib.request
from fetch_sources import entries, matches, sha256, extract_cmp


def fetch_archive(root, workers=12):
    root=Path(root).resolve()
    manifest=json.loads((root/'methods/sources.json').read_text())
    entry=next(e for e in entries(manifest) if e['path'].endswith('cmp_rnaseq_all_20220624.zip'))
    output=root/'inputs'/entry['path']
    if matches(output,entry):
        return extract_cmp(root/'inputs',manifest)
    if output.exists():
        raise ValueError('Existing CMP archive has different bytes')
    parts=output.parent/(output.name+'.ranges');parts.mkdir(parents=True,exist_ok=True)
    size=32*1024*1024
    spans=[(i,start,min(start+size,entry['bytes'])-1) for i,start in enumerate(range(0,entry['bytes'],size))]
    def one(span):
        i,start,end=span;path=parts/f'{i:04d}'
        expected=end-start+1
        if path.exists() and path.stat().st_size==expected:return path
        if path.exists() and path.stat().st_size>expected:raise ValueError('Oversized range fragment')
        failures=0
        while not path.exists() or path.stat().st_size<expected:
            offset=start+(path.stat().st_size if path.exists() else 0)
            stop=min(offset+4*1024*1024-1,end)
            try:
                req=urllib.request.Request(entry['url'],headers={'Range':f'bytes={offset}-{stop}','User-Agent':'STATE-historical-reconstruction/1.0'})
                with urllib.request.urlopen(req,timeout=90) as response:
                    if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {offset}-{stop}/{entry["bytes"]}':
                        raise ValueError('Server did not honor the exact requested byte range')
                    count=0
                    with path.open('ab') as stream:
                        while True:
                            block=response.read(128*1024)
                            if not block:break
                            count+=len(block)
                            if count>stop-offset+1:raise ValueError('Oversized range response')
                            stream.write(block)
                if count!=stop-offset+1:raise ValueError('Incomplete CMP byte range; resuming retained bytes')
                failures=0
            except Exception as error:
                failures+=1
                print(json.dumps({'event':'range_retry','range':i,'offset':offset,'error':str(error)}),flush=True)
                if failures>=12:raise
                time.sleep(min(10,failures*2))
        print(json.dumps({'event':'range_complete','range':i,'bytes':path.stat().st_size}),flush=True)
        return path
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(workers,16))) as pool:
        list(pool.map(one,spans))
    temporary=output.with_name(output.name+'.assembled')
    with temporary.open('wb') as stream:
        for i,_,_ in spans:
            with (parts/f'{i:04d}').open('rb') as part:
                for block in iter(lambda:part.read(8*1024*1024),b''):stream.write(block)
    if not matches(temporary,entry):
        temporary.unlink(missing_ok=True)
        raise ValueError('Assembled CMP source does not match the original SHA-256')
    os.replace(temporary,output)
    for i,_,_ in spans:(parts/f'{i:04d}').unlink()
    parts.rmdir()
    result=extract_cmp(root/'inputs',manifest)
    print(json.dumps({'event':'archive_verified','path':entry['path'],'sha256':sha256(output),'member':result}),flush=True)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--workers',type=int,default=12)
    args=parser.parse_args();fetch_archive(args.root,args.workers)
