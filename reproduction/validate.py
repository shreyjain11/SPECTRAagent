"""Check records, notebook evidence, payload hashes and workflow traceability.

Does not execute scientific analyses or grade the original conclusions.
"""
import argparse,ast,gzip,hashlib,json,re
from collections import Counter
from functools import lru_cache
from pathlib import Path

ROOT=Path(__file__).resolve().parent
RICH_FORMATS={'recovered_historical_notebook','source_workflow_notebook'}
SOURCE_WORKFLOW_IDS=({f'state-codex-r1/test-{i:02d}' for i in range(1,5)}
                     | {f'state-codex-r2/test-{i:02d}' for i in range(1,6)})
def read(path):return json.loads((ROOT/path).read_text())
def file(path):
    p=(ROOT/path).resolve()
    assert p.is_relative_to(ROOT) and p.is_file(),path
    return p
@lru_cache(None)
def digest(path):return hashlib.sha256(file(path).read_bytes()).hexdigest()

def check_public_archives(sources):
    data=read('data.json');archives={item['id']:item for item in data['archives']}
    assert len(archives)==len(data['archives'])==4
    for model in ['state','conch','esmfold2','alphamissense']:
        archive=archives[f'{model}-retained-inputs']
        assert archive['model']==model and archive['id'] in sources
        assert all(archive[key]==sources[archive['id']][key] for key in ['url','bytes','sha256'])
        assert re.fullmatch('[a-f0-9]{64}',archive['sha256'])
        inventory=read(f'inputs/{model}.json')
        assert len(inventory)==archive['files']
        assert len({item['path'] for item in inventory})==len(inventory)
        assert sum(item['bytes'] for item in inventory)==archive['uncompressed_bytes']
        assert all(item['download_source']==archive['id'] for item in inventory)
        assert all(re.fullmatch('[a-f0-9]{64}',item['sha256']) for item in inventory)
    return data,archives

def check_legacy_notebook(record,archives):
    """The public archive preparation contract applies to the retained export.

    Primary records additionally offer a richer notebook with a separate input
    bootstrap. Its first cell is not the legacy public archive preparation cell.
    """
    split=record['dataset_split'];public=split['public_inputs']
    assert public['archive'] in archives and public['notebook_preparation_cell']==0
    file(public['prepare']);file(public['catalog'])
    name=public.get('implementation','implementation')
    assert name in ['implementation','legacy_implementation'],(record['id'],name)
    rich=record['implementation'].get('format') in RICH_FORMATS
    assert name==('legacy_implementation' if rich else 'implementation'),record['id']
    impl=record[name];assert impl['notebook'].startswith('materials/'),impl['notebook']
    assert digest(impl['notebook'])==impl['published_notebook_sha256'],impl['notebook']
    book=read(impl['notebook']);assert book['nbformat']==4
    assert f"prepare_notebook({record['id']!r})" in ''.join(book['cells'][0]['source']),record['id']
    assert all(c['cell_type']=='code' and c['execution_count'] is None and c['outputs']==[] for c in book['cells'])
    assert len(book['cells'])==impl['saved_code_cells'] and impl['saved_error_outputs']==0
    ast.parse(file(impl['script']).read_text())
    for item in read(impl['supporting_code']):assert digest(item['path'])==item['sha256'],item['path']
    expected_inventory=f"inputs/{archives[public['archive']]['model']}.json"
    inventory=split['legacy_input_inventory'] if rich else split['input_inventory']
    assert inventory==expected_inventory,(record['id'],inventory)
    return impl,book

def check_legacy_execution(implementations,data,archives,staged):
    """Bind the original143 execution receipts to materials/, never rich notebooks."""
    execution=read('execution.json')
    assert execution['input_release']==data['release']
    results={row['id']:row for row in execution['results']}
    assert len(results)==len(execution['results'])==execution['notebooks_executed']==143
    assert set(results)==set(implementations)
    for identifier,(impl,book) in implementations.items():
        result=results[identifier]
        assert result['notebook']==impl['notebook'],identifier
        assert digest(impl['notebook'])==result['notebook_sha256'],identifier
        calculations=[''.join(c['source']) for c in book['cells'][1:] if c['cell_type']=='code']
        encoded=json.dumps(calculations,separators=(',',':')).encode()
        assert hashlib.sha256(encoded).hexdigest()==result['calculation_cells_sha256'],identifier
        assert result['error'] is None and result['executed_cells']==len(book['cells']),identifier
    receipts={row['id']:row for row in execution['public_download_verification']}
    assert len(receipts)==len(execution['public_download_verification'])==4
    assert set(receipts)==set(archives)
    for identifier,archive in archives.items():
        if identifier in staged:continue
        receipt=receipts[identifier]
        assert all(receipt[key]==archive[key] for key in ['url','bytes','sha256']),identifier
        assert receipt['http_status']==200 and receipt['anonymous_access_observed'] is True
        assert receipt['checked_at']
    for name in ['repository_root','repeat_in_same_namespace']:
        assert execution['preparation_checks'][name]==143
    return len(results)

def check_payloads():
    checked=0
    esm=read('primary/esmfold2/artifact_manifest.json')
    # The model-specific bootstrap verifies its content-addressed objects and
    # restored paths; this check verifies the Git-distributed archive itself.
    assert digest('primary/esmfold2/'+esm['archive'])==esm['archive_sha256']
    assert file('primary/esmfold2/'+esm['archive']).stat().st_size==esm['archive_bytes']
    checked+=1
    for item in read('primary/conch/PAYLOAD_MANIFEST.json'):
        assert digest('primary/conch/'+item['archive'])==item['archive_sha256']
        assert file('primary/conch/'+item['archive']).stat().st_size==item['archive_bytes']
        checked+=1
    for model in ['state','alphamissense']:
        for item in read(f'primary/{model}/payload_manifest.json')['assets']:
            assert re.fullmatch('[0-9a-f]{64}',item['sha256'])
            if item.get('path'):
                path=f"primary/{model}/"+item['path']
                assert digest(path)==item['sha256'],path
                assert file(path).stat().st_size==item['bytes'],path
                checked+=1
            else:
                assert item['url'].startswith('https://github.com/yashaektefaie/SPECTRAagent/releases/download/'),item
                assert item['publication_status']=='verified_public',item['name']
                receipt=read(f'primary/{model}/'+item['publication_evidence'])
                assert all(receipt[k]==item[k] for k in ['url','bytes','sha256'])
                assert receipt['anonymous_head_status']==200
                assert receipt['anonymous_content_length']==item['bytes']
                assert receipt['github_upload_digest_verified'] is True
    return checked

def check_inline(record, entry):
    """Check the preferred executable notebook separately from supporting files."""
    from integrate_inline import code_review
    implementation=record.get('inline_implementation')
    if not implementation:
        assert entry['notebook'] is None,record['id']
        assert entry['inline_status'].startswith('pending'),record['id']
        return False
    assert implementation['format']=='inline_analysis_notebook'
    assert entry['notebook']==implementation['notebook']
    assert digest(implementation['notebook'])==implementation['published_notebook_sha256']
    assert digest(implementation['html'])==implementation['published_html_sha256']
    receipt=read(implementation['execution_evidence'])
    assert receipt['analysis_id']==record['id'] and receipt['completed']
    assert 'exxact05' in receipt['host'].lower()
    assert receipt['notebook_sha256']==digest(implementation['notebook'])
    assert receipt['html_sha256']==digest(implementation['html'])
    sections,code=code_review(read(implementation['notebook']))
    assert sections==implementation['sections']==receipt['sections']
    assert len(code)==implementation['code_cells']==receipt['code_cells']==receipt['executed_cells']
    assert not receipt['errors']
    assert receipt['result_location']==implementation['calculated_result']
    for item in receipt.get('calculation_evidence',[])+receipt.get('input_manifests',[]):
        assert digest(item['path'])==item['sha256']
    return True

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
    data,archives=check_public_archives({item['id']:item for item in sources})
    count=0;cells=0;primary=0;inline=0;ids=set();primaryids=set();sourceids_reconstructed=set();models={};samplefiles=set();legacy={}
    decisions={d['id']:d for d in read(index['historical_decisions'])['records']}
    for investigation in index['investigations']:
        for entry in investigation['analyses']:
            d=read(entry['path']);assert d['id']==entry['id'] and d['id'] not in ids;ids.add(d['id'])
            assert d['investigation']==investigation['id']
            assert not {'status','verdict','grade','pass','fail','accepted','rejected'}&d.keys()
            for name in ['dataset_split','axis_levels','model_evaluation','curve','insight']:
                assert isinstance(d[name],dict) and d[name],(entry['path'],name)
            assert set(d['dataset_split']['public_sources'])<=sourceids
            file(d['dataset_split']['input_inventory'])
            legacy[d['id']]=check_legacy_notebook(d,archives)
            for s in d['dataset_split']['sample_tables']:
                assert digest(s['path'])==s['sha256']
                if s['path'] not in samplefiles:
                    table=json.loads(gzip.decompress(file(s['path']).read_bytes()))
                    assert len(table['rows'])==s['rows'] and table['columns']==s['columns']
                    assert all(set(row)==set(s['columns']) for row in table['rows'])
                    samplefiles.add(s['path'])
            impl=d['implementation'];assert digest(impl['notebook'])==impl['published_notebook_sha256']
            b=read(impl['notebook']);assert b['nbformat']==4
            code=[c for c in b['cells'] if c['cell_type']=='code']
            if impl.get('format') in RICH_FORMATS:
                if impl['format']=='recovered_historical_notebook':
                    primary+=1;primaryids.add(d['id'])
                else:
                    assert d['id'] in SOURCE_WORKFLOW_IDS,d['id']
                    sourceids_reconstructed.add(d['id'])
                assert any(c['cell_type']=='markdown' for c in b['cells']),impl['notebook']
                assert not [o for c in code for o in c.get('outputs',[]) if o.get('output_type')=='error']
                assert digest(impl['script'])==impl['published_script_sha256']
                assert len(impl['cell_locations'])==len(code)
                recovered=d['primary_recovery'] if impl['format']=='recovered_historical_notebook' else d['workflow_reconstruction']
                file(recovered['traceability'])
                assert set(recovered['stages'])=={'data','processing','axis','levels','evaluation','curve','decision'}
                assert all(recovered['stages'].values())
                if impl['format']=='source_workflow_notebook':
                    assert all(c['execution_count'] is not None for c in code),impl['notebook']
                    receipt=read(recovered['execution_evidence'])
                    assert receipt['status']=='all_notebooks_executed_and_exported'
                    matches=[r for r in receipt['notebooks'] if r['notebook']==Path(impl['notebook']).name]
                    assert len(matches)==1 and matches[0]['sha256']==digest(impl['notebook'])
                    assert matches[0]['execution']['completed'] is True
                    assert matches[0]['error_outputs']==0
                    pipeline=read(recovered['pipeline_execution_evidence'])
                    assert pipeline['completed'] and pipeline['derived_stage_policy']=='recompute_from_source_inputs'
                    assert 'exxact05' in pipeline['host'].lower()
                    if 'stage_execution_evidence' in recovered:
                        receipts=recovered['stage_execution_evidence']
                        assert receipts and len(receipts)==len(pipeline['receipts'])
                        assert not pipeline['reused_stages']
                        assert pipeline['historical_outputs_used_to_drive_calculations'] is False
                        for saved,original in zip(receipts,pipeline['receipts']):
                            assert saved['sha256']==original['sha256']==digest(saved['path'])
                            analysis=read(saved['path'])
                            assert analysis['status']=='computed_from_public_inputs'
                            assert 'exxact05' in analysis['scientific_execution_host'].lower()
                            assert analysis['historical_outputs_used_as_calculation_inputs'] is False
                            package=Path(recovered['package_manifest']).parent
                            for relative,expected in analysis['methods'].items():
                                assert digest(str(package/relative))==expected
                            for output in analysis['outputs']:
                                assert digest(str(package/output['path']))==output['sha256']
                    else:
                        analysis=read(recovered['analysis_execution_evidence'])
                        assert analysis['completed'] and analysis['scientific_workflow_executed']
                        assert analysis['historical_aggregate_fallback'] is False
                    trace=read(recovered['traceability'])
                    assert trace['historical_aggregates_used_as_calculation_inputs'] is False
                    assert trace['scientific_execution_host']=='exxact05'
                    for item in read(recovered['package_manifest'])['files']:
                        assert digest(item['path'])==item['sha256'],item['path']
            else:
                assert all(c['cell_type']=='code' and c['execution_count'] is None and c['outputs']==[] for c in b['cells'])
            assert len(code)==impl['saved_code_cells'] and impl['saved_error_outputs']==0
            ast.parse(file(impl['script']).read_text())
            for s in read(impl['supporting_code']):assert digest(s['path'])==s['sha256']
            for s in d['model_evaluation']['fine_tuning']['comparators']:file(s['evidence'])
            assert d['historical_decision']['record_id']==d['id']
            assert d['historical_decision']['result']==decisions[d['id']]['historical_result']
            if index.get('preferred_notebook_format')=='inline_analysis_notebook':
                inline+=check_inline(d,entry)
                assert entry['supporting_notebook']==impl['notebook']
            else:
                assert entry['notebook']==impl['notebook']
            cells+=len(code);count+=1;models[investigation['model']]=models.get(investigation['model'],0)+1
    assert len(index['investigations'])==28 and count==143 and primary==44
    legacy_cells=sum(len(book['cells']) for _,book in legacy.values())
    assert legacy_cells==756
    executed=check_legacy_execution(legacy,data,archives,staged)
    assert models=={'ESMFold2':35,'STATE':44,'CONCH':30,'AlphaMissense':34}
    assert {d['id'] for d in read('reconstruction.json')}==ids
    review=read(index['traceability_review'])
    assert {d['id'] for d in review['entries']}==ids==set(decisions)
    assert review['scientific_adjudication_performed'] is False
    expected_counts={'primary_workflow_packaged':44,'original_records_missing':67-len(sourceids_reconstructed),'calculation_replay_packaged':32}
    if sourceids_reconstructed:
        assert sourceids_reconstructed==SOURCE_WORKFLOW_IDS
        expected_counts['source_workflow_reconstructed']=len(sourceids_reconstructed)
    assert review['counts']==expected_counts
    assert dict(Counter(row['coverage'] for row in review['entries']))==review['counts']
    assert all(set(row['stages'])==set(review['criteria']) for row in review['entries'])
    nonprimary=read('NONPRIMARY_REVIEW.json')
    nonprimary_ids={row['analysis_id'] for row in nonprimary['analyses']}
    assert len(nonprimary['analyses'])==len(nonprimary_ids)==nonprimary['counts']['reviewed']==99
    assert nonprimary_ids==ids-primaryids
    nonprimary_counts=Counter(row['category'] for row in nonprimary['analyses'])
    expected_nonprimary={k:v for k,v in expected_counts.items() if k!='primary_workflow_packaged'}
    assert nonprimary_counts==expected_nonprimary
    assert all(nonprimary['counts'][category]==number for category,number in nonprimary_counts.items())
    file(index['primary_workflows'])
    payloads=check_payloads()
    if index.get('preferred_notebook_format')=='inline_analysis_notebook':
        preferred=read(index['preferred_notebooks'])
        file(index['preferred_notebook_guide'])
        file(index['preferred_workflow_review'])
        assert {row['id'] for row in preferred['analyses']}==ids
        assert sum(bool(row['notebook']) for row in preferred['analyses'])==inline
        assert dict(Counter(row['status'] for row in preferred['analyses']))==preferred['counts']
        print(json.dumps({'preferred_inline_notebooks_verified':inline,'preferred_pending':count-inline,'inline_status':preferred['counts']},indent=2))
    print(json.dumps({'investigations':28,'analyses':count,'primary_workflows':primary,'source_workflows_reconstructed':len(sourceids_reconstructed),'code_cells':cells,'legacy_materials_code_cells':legacy_cells,'legacy_execution_receipts_verified':executed,'public_sources':len(sources),'public_input_archives':len(archives),'downloads_not_yet_publicly_verified':staged,'linked_sample_tables':len(samplefiles),'payloads_verified':payloads,'traceability_review':review['counts'],'nonprimary_review':dict(nonprimary_counts),'per_model':models},indent=2))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--allow-staged-downloads',action='store_true',help='Check prepared legacy archive metadata before publishing; report unverified archives explicitly.')
    args=parser.parse_args();main(args.allow_staged_downloads)
