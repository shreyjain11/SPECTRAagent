"""Download the exact documented public input set into the execution host."""
from pathlib import Path
import argparse, concurrent.futures, json, time
from fetch_sources import entries, fetch, extract_cmp, sha256

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args();root=args.root.resolve();dest=root/'inputs'
    manifest_path=root/'methods/sources.json';manifest=json.loads(manifest_path.read_text())
    selected=entries(manifest);receipts=[];errors=[]
    print(json.dumps({'event':'start','files':len(selected),'bytes':sum(e['bytes'] for e in selected),'destination':str(dest)}),flush=True)
    def one(entry):
        for attempt in range(3):
            try:
                if entry['path'].endswith('cmp_rnaseq_all_20220624.zip'):
                    from fetch_cmp_ranges import fetch_archive
                    fetch_archive(root)
                    result={'path':entry['path'],'status':'verified_archive_and_member'}
                else:
                    result=fetch(entry,dest)
                return {**result,'bytes':entry['bytes'],'sha256':entry['sha256'],'url':entry['url']}
            except Exception:
                if attempt==2:raise
                time.sleep(2*(attempt+1))
    dest.mkdir(parents=True,exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(args.workers,8))) as pool:
        tasks={pool.submit(one,e):e for e in selected}
        for future in concurrent.futures.as_completed(tasks):
            entry=tasks[future]
            try:
                result=future.result();receipts.append(result)
                print(json.dumps({'event':'verified','completed':len(receipts),'path':entry['path'],'bytes':entry['bytes']}),flush=True)
                if entry['path'].endswith('cmp_rnaseq_all_20220624.zip'):
                    print(json.dumps(extract_cmp(dest,manifest)),flush=True)
            except Exception as error:
                errors.append({'path':entry['path'],'error':str(error)})
                print(json.dumps({'event':'error',**errors[-1]}),flush=True)
            receipt={'source_manifest_sha256':sha256(manifest_path),'completed':len(receipts)==len(selected) and not errors,'files':receipts,'errors':errors}
            temporary=dest/'DOWNLOAD_RECEIPT.json.part';temporary.write_text(json.dumps(receipt,indent=2)+'\n');temporary.replace(dest/'DOWNLOAD_RECEIPT.json')
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
