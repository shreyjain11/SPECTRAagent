"""Check the published record contract; does not execute scientific analyses."""
import argparse,ast,gzip,hashlib,json,re
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def read(path):return json.loads((ROOT/path).read_text())
def file(path):
    p=(ROOT/path).resolve()
    assert p.is_relative_to(ROOT) and p.is_file(),path
    return p
@lru_cache(None)
def digest(path):return hashlib.sha256(file(path).read_bytes()).hexdigest()

def main(allow_staged_downloads=False):
    index=read('index.json');sources=read(index['sources']);sourceids={x['id'] for x in sources}
    assert len(sourceids)==len(sources)
    staged=[]
    for s in sources:
        assert s['url'].startswith('https://')
        if allow_staged_downloads and s['id'].endswith('-retained-inputs') and not s['anonymous_access_observed']:
            staged.append(s['id'])
        else:
            assert s['anonymous_access_observed'] is True and s['http_status']==200 and s['checked_at']
        assert not re.search(r'(?:token|api_key|signature)=',s['url'],re.I)
    data=read('data.json');archives={entry['id']:entry for entry in data['archives']}
    assert len(archives)==4
    for model in ['state','conch','esmfold2','alphamissense']:
        inventory=read(f'inputs/{model}.json')
        archive=archives[f'{model}-retained-inputs']
        assert archive['model']==model and archive['id'] in sourceids
        assert len(inventory)==archive['files']
        assert all(entry['download_source']==archive['id'] for entry in inventory)
        assert all(re.fullmatch('[a-f0-9]{64}',entry['sha256']) for entry in inventory)
    count=0;cells=0;ids=set();models={};samplefiles=set()
    for investigation in index['investigations']:
        for entry in investigation['analyses']:
            d=read(entry['path']);assert d['id']==entry['id'] and d['id'] not in ids;ids.add(d['id'])
            assert d['investigation']==investigation['id']
            assert not {'status','verdict','grade','pass','fail','accepted','rejected'}&d.keys()
            for name in ['dataset_split','axis_levels','model_evaluation','curve','insight']:
                assert isinstance(d[name],dict) and d[name],(entry['path'],name)
            assert set(d['dataset_split']['public_sources'])<=sourceids
            file(d['dataset_split']['input_inventory'])
            public=d['dataset_split']['public_inputs']
            assert public['archive'] in archives and public['notebook_preparation_cell']==0
            file(public['prepare']);file(public['catalog'])
            for s in d['dataset_split']['sample_tables']:
                assert digest(s['path'])==s['sha256']
                if s['path'] not in samplefiles:
                    table=json.loads(gzip.decompress(file(s['path']).read_bytes()))
                    assert len(table['rows'])==s['rows'] and table['columns']==s['columns']
                    assert all(set(row)==set(s['columns']) for row in table['rows'])
                    samplefiles.add(s['path'])
            impl=d['implementation'];assert digest(impl['notebook'])==impl['published_notebook_sha256']
            b=read(impl['notebook']);assert b['nbformat']==4
            assert f"prepare_notebook({d['id']!r})" in ''.join(b['cells'][0]['source'])
            assert all(c['cell_type']=='code' and c['execution_count'] is None and c['outputs']==[] for c in b['cells'])
            assert len(b['cells'])==impl['saved_code_cells'] and impl['saved_error_outputs']==0
            ast.parse(file(impl['script']).read_text())
            for s in read(impl['supporting_code']):assert digest(s['path'])==s['sha256']
            for s in d['model_evaluation']['fine_tuning']['comparators']:file(s['evidence'])
            cells+=len(b['cells']);count+=1;models[investigation['model']]=models.get(investigation['model'],0)+1
    assert len(index['investigations'])==28 and count==143 and cells==756
    assert models=={'ESMFold2':35,'STATE':44,'CONCH':30,'AlphaMissense':34}
    assert {d['id'] for d in read('reconstruction.json')}==ids
    print(json.dumps({'investigations':28,'analyses':count,'code_cells':cells,'public_sources':len(sources),'downloads_not_yet_publicly_verified':staged,'linked_sample_tables':len(samplefiles),'per_model':models},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-staged-downloads',action='store_true',help='Check a prepared revision before publishing its data release; unverified archives are reported.')
    args=parser.parse_args();main(args.allow_staged_downloads)
