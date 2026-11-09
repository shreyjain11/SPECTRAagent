"""Refresh primary records and a workflow-only review of all 143 PR entries.

Uses only packaged evidence. Does not execute models, invent missing analyses,
or apply additional scientific acceptance criteria.
"""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
GROUPS = {'esmfold2-featured': 'esmfold2', 'state-featured': 'state',
          'conch-primary': 'conch', 'am-primary': 'alphamissense'}
STAGES = ['data', 'processing', 'axis', 'levels', 'evaluation', 'curve', 'decision']
REPORT_ONLY = {
    'esmfold2-codex-r1', 'esmfold2-codex-r2', 'esmfold2-opus-r1', 'esmfold2-opus-r2',
    'state-codex-r1', 'state-codex-r2', 'state-kimi-r2',
    'conch-gpt-r1', 'conch-gpt-r2', 'conch-kimi-r1',
    'am-gpt-r1', 'am-gpt-r2', 'am-kimi-r1', 'am-kimi-r2',
}


def read(path):
    return json.loads((ROOT / path).read_text())


def write(path, data):
    (ROOT / path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


def digest(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def trace_entries(model):
    doc = read(f'primary/{model}/traceability.json')
    published_path = ROOT / f'primary/{model}/PUBLISHED_NOTEBOOKS.json'
    published = {row['notebook']: row for row in json.loads(published_path.read_text())} if published_path.is_file() else {}
    rows = doc.get('entries', doc.get('analyses'))
    assert rows, model
    normalized = {}
    for row in rows:
        ident = row.get('id', row.get('analysis_id'))
        stages = row.get('stages', row)
        normalized[ident] = {
            'notebook': row['notebook'],
            'script': row.get('script', row.get('code_export')),
            'cell_locations': row.get('cell_locations', published.get(row['notebook'], {}).get('cell_locations', [])),
            'stages': {name: stages.get(name, stages.get({
                'curve': 'curves_and_diagnostics', 'decision': 'historical_decision',
            }.get(name, name))) for name in STAGES},
        }
        assert all(normalized[ident]['stages'].values()), (model, ident)
    return normalized


def supporting_code(model):
    prefix = f'primary/{model}'
    files = subprocess.check_output(
        ['git', 'ls-files', '--cached', '--others', '--exclude-standard', '--', prefix],
        cwd=ROOT, text=True).splitlines()
    rows = [{'path': path, 'sha256': digest(path)} for path in sorted(set(files))
            if path.endswith('.py')]
    assert rows, model
    output = f'code/primary-{model}.json'
    write(output, rows)
    return output


def main():
    index = read('index.json')
    decisions = {row['id']: row for row in read('historical_decisions.json')['records']}
    traces = {group: trace_entries(model) for group, model in GROUPS.items()}
    support = {model: supporting_code(model) for model in GROUPS.values()}
    review = []
    reconstruction = []
    for inv in index['investigations']:
        group = inv['id']
        for link in inv['analyses']:
            record = read(link['path'])
            ident = record['id']
            record['historical_decision'] = {
                'source': 'historical_decisions.json', 'record_id': ident,
                'disposition': decisions[ident]['historical_disposition'],
                'result': decisions[ident]['historical_result'],
                'attribution': 'Recorded historical registry summary; not a new reviewer verdict',
            }
            if group in GROUPS:
                model = GROUPS[group]
                package = f'primary/{model}'
                trace = traces[group][ident]
                notebook = f"{package}/{trace['notebook']}"
                script = f"{package}/{trace['script']}"
                nb = read(notebook)
                cells = [c for c in nb['cells'] if c['cell_type'] == 'code']
                errors = [o for c in cells for o in c.get('outputs', []) if o.get('output_type') == 'error']
                assert not errors, ident
                record.setdefault('legacy_implementation', record['implementation'])
                record.setdefault('legacy_reconstruction_notes', record['reconstruction_notes'])
                record['implementation'] = {
                    'format': 'recovered_historical_notebook', 'notebook': notebook,
                    'script': script, 'supporting_code': support[model],
                    'published_notebook_sha256': digest(notebook),
                    'published_script_sha256': digest(script),
                    'cell_locations': trace['cell_locations'],
                    'saved_code_cells': len(cells), 'saved_error_outputs': len(errors),
                    'saved_figures': sum('image/png' in o.get('data', {}) for c in cells for o in c.get('outputs', [])),
                    'changes': ['Recovered original inputs and programs are packaged or acquired with content checks.',
                                'Markdown, original decisions and selected historical outputs are retained.',
                                'Default replay and optional full raw-data/model execution are explicitly distinguished.'],
                }
                record['primary_recovery'] = {
                    'package': package, 'traceability': f'{package}/traceability.json',
                    'record_id': ident, 'evidence_paths_relative_to': package,
                    'stages': trace['stages'],
                }
                record['dataset_split']['description'] = 'Original frozen records and source identities are preserved; packaged inputs and executable acquisition steps are documented in the linked recovery chain.'
                record['dataset_split'].setdefault('legacy_input_inventory', record['dataset_split']['input_inventory'])
                record['dataset_split']['input_inventory'] = f"{package}/" + {
                    'esmfold2': 'artifact_manifest.json', 'conch': 'PAYLOAD_MANIFEST.json',
                    'state': 'payload_manifest.json', 'alphamissense': 'payload_manifest.json',
                }[model]
                record['dataset_split']['recovered_workflow'] = f'{package}/traceability.json'
                record['dataset_split']['public_inputs']['implementation'] = 'legacy_implementation'
                record['dataset_split']['public_inputs']['scope'] = 'Retained public-bundle notebook; the preferred primary notebook uses its own package bootstrap.'
                record['axis_levels']['calculation'] = 'Original feature/level construction or explicitly preserved frozen memberships; exact source functions and inputs are linked in primary_recovery.stages.'
                for section in ['axis_levels', 'model_evaluation', 'curve', 'insight']:
                    record[section]['code'] = script
                record['model_evaluation']['measurements'] = {
                    'state': 'Original released per-record evaluation scores, processed as the original agent did; no fresh STATE inference is required for this workflow.',
                    'alphamissense': 'Original released AlphaMissense predictions, benchmark joins and original comparator calculations; fresh target-model inference was not part of this workflow.',
                    'conch': 'Original target logits/labels and both follow-up panels are packaged. Pinned image acquisition, original CONCH scoring and analysis are connected in optional full-workflow mode.',
                    'esmfold2': 'Original individual model measurements and scoring/selection code are packaged. The optional full-workflow route uses the documented current implementation with pinned original weights.',
                }[model]
                record['curve']['aggregation_and_uncertainty'] = 'Original curves, controls and selection calculations are traceable to retained individual measurements. Any added display diagnostics are labelled separately; prescoring rejections retain their actual diagnostic.'
                record['insight']['comparison_controls_confirmation'] = 'Original comparisons and decision evidence are preserved. The historical decision is not reassigned from a new model run or an additional protocol review.'
                record['reconstruction_notes'] = {
                    'state': ['The workflow intentionally starts from the official scored files used by the original agent. Exact similarity ties can change nearest-drug names without changing values, levels or curves.'],
                    'alphamissense': ['Some large public-download/preparation steps have not been rerun in full. The default replay uses the exact retained inputs supplied by the package/bootstrap.', 'The original OTU7A weighted-feature discrepancy is preserved and documented; AlphaMissense results are unchanged and one comparator interval bound differs by 0.0001.'],
                    'conch': ['The full target-image download and new CONCH inference route is connected but has not been executed during this integration. It requires the documented model access and environment.', 'The reconstructed reference matrix has been validated against original level assignments and comparator labels. Optional raw-pixel checks are distinguished from default retained-input replay.'],
                    'esmfold2': ['The full bulk-download/raw-feature/current-model route is connected but was not executed during this integration.', 'Historical results used the older Biohub fork. The current implementation uses pinned original model sources; completed conversion validation checked tensor keys/shapes, not independent saved-value or prediction equality.', 'Original frozen memberships and per-analysis metadata missingness are preserved, including the documented flexible-axis boundary case.'],
                }[model]
                item = {'id': ident, 'axis': record['axis'], 'coverage': 'primary_workflow_packaged',
                        'notebook': notebook, 'traceability': f'{package}/traceability.json',
                        'stages': {key: 'linked_in_primary_recovery' for key in STAGES},
                        'execution_limits': record['reconstruction_notes'], 'remaining_traceability_gaps': []}
            else:
                missing = group in REPORT_ONLY or ident == 'conch-kimi-r2/test-02'
                item = {'id': ident, 'axis': record['axis'],
                        'coverage': 'original_records_missing' if missing else 'calculation_replay_packaged',
                        'notebook': record['implementation']['notebook'],
                        'stages': {'data': 'public_checksum_verified_retained_input_archive',
                                   'processing': 'missing_original_inputs_or_code' if missing else 'retained_calculations_with_portable_input_bootstrap',
                                   'axis': 'recorded_definition',
                                   'levels': 'original_individual_construction_missing' if missing else 'retained_calculation_or_frozen_memberships',
                                   'evaluation': 'original_individual_computation_missing' if missing else 'retained_measurements_or_released_scores',
                                   'curve': 'summary_or_evidence_display_only' if missing else 'executable_calculation_with_original_and_added_diagnostics_distinguished',
                                   'decision': 'attributed_historical_summary'},
                        'public_inputs': record['dataset_split']['public_inputs'],
                        'execution_evidence': 'execution.json',
                        'independent_review': 'NONPRIMARY_REVIEW.json',
                        'remaining_traceability_gaps': [
                            'The public archive enables execution of the retained evidence/summary display; original individual inputs and/or calculations remain missing.'
                        ] if missing else [],
                        'coverage_limit': 'Executable retained calculation replay; complete original provenance is not certified. See per-entry review and original reconstruction notes. Scientific corrections or experiments not originally performed are not reproduction requirements.',
                        'original_reconstruction_notes': record['reconstruction_notes']}
                record['traceability_review'] = {
                    'coverage': item['coverage'], 'review': 'traceability_review.json',
                    'record_id': ident,
                    'scope': 'Original-workflow traceability only. New confirmation studies, corrected scientific conclusions and fresh inference not performed originally are not requirements.'}
            link['notebook'] = record['implementation']['notebook']
            link['traceability_coverage'] = item['coverage']
            write(link['path'], record)
            review.append(item)
            reconstruction.append({'id': ident, 'notes': record['reconstruction_notes']})
    counts = {kind: sum(row['coverage'] == kind for row in review) for kind in
              ['primary_workflow_packaged', 'original_records_missing', 'calculation_replay_packaged']}
    assert counts == {'primary_workflow_packaged': 44, 'original_records_missing': 67,
                      'calculation_replay_packaged': 32}, counts
    index.update(schema_version=2, historical_decisions='historical_decisions.json',
                 traceability_review='traceability_review.json', primary_workflows='primary/README.md')
    write('index.json', index)
    write('reconstruction.json', reconstruction)
    write('traceability_review.json', {
        'review_scope': 'All 143 PR entries: original data acquisition, processing, axis definition, levels, measurements, curves/diagnostics and historical decision.',
        'scientific_adjudication_performed': False, 'counts': counts,
        'criteria': STAGES,
        'interpretation': 'Coverage is not a new scientific verdict. Lack of fresh inference is not a gap when the original workflow consumed released scores. Prescoring rejections require their original diagnostic, not an invented performance curve. New independent confirmation and correction of historical scientific errors are not imposed as reproduction requirements.',
        'entries': review})
    print(json.dumps(counts, indent=2))


if __name__ == '__main__':
    main()
