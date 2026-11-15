"""Check corrected AlphaMissense metadata against saved outputs, without inference.

The historical fingerprints below bind the preserved supporting scientific fields
from PR revision bda8adc. This is a metadata/integrity check, not a new execution
of the scientific workflows.
"""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCIENTIFIC = ('dataset_split', 'axis_levels', 'model_evaluation', 'curve', 'insight')
PRESERVED = SCIENTIFIC + ('reconstruction_notes', 'historical_decision',
                          'implementation', 'inline_implementation')
EXPECTED_PRESERVED_SHA256 = {'am-opus-r1/test-01': '8ef39589cdc78c52b9242164ed761c32d562b3e0b005b215017f438816273379', 'am-opus-r1/test-02': 'e5bd1eaeac10b85b3b6260cd8d8101b97783163c7bba271e02066b1a8c887b89', 'am-opus-r1/test-03': 'e696e20553e3fcd6b127dafc535506edf69767715bc20b1c539636d125f8071b', 'am-opus-r2/test-01': '695deccf39c0e1cd53dd099f5777d5ca4de4abda7129e65bc2152dc14cb0dcaf', 'am-opus-r2/test-02': '49ba24535917731c306a2eb3abdf582c52f4649afc70f80dceaf6fdb52f923b6', 'am-opus-r2/test-03': 'b74569bf8f562e3fa4e81c18c03017ebcae63a4b96c6b43cf34b272890449612'}
NUMBER = r'-?\d+(?:\.\d+)?'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def output_text(output):
    data = output.get('data', {})
    return ''.join(output.get('text', data.get('text/markdown', data.get('text/plain', []))))


def verify(root=ROOT):
    checked = []
    for identifier, expected_historical_hash in EXPECTED_PRESERVED_SHA256.items():
        record = json.loads((root / 'analyses' / (identifier + '.json')).read_text())
        preserved = {key: record[key] for key in PRESERVED}
        for key in SCIENTIFIC:
            preserved[key] = dict(preserved[key])
            assert preserved[key].pop('scope') == 'supporting_historical_analysis', (identifier, key)
        historical_hash = hashlib.sha256(json.dumps(
            preserved, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
        assert historical_hash == expected_historical_hash, (identifier, 'historical fields changed')
        assert record['reconstruction_notes_scope']['scope'] == 'supporting_historical_analysis'
        current = record['current_inline_analysis']
        evidence = current['evidence']
        notebook_path = root / evidence['notebook']
        assert digest(notebook_path) == evidence['notebook_sha256']
        assert digest(root / evidence['execution_record']) == evidence['execution_record_sha256']
        assert evidence['notebook'] == record['inline_implementation']['notebook']
        notebook = json.loads(notebook_path.read_text())
        outputs = [(index, output_text(output))
                   for index, cell in enumerate(notebook['cells'])
                   for output in cell.get('outputs', [])]
        joined = [(index, text) for index, text in outputs
                  if text.startswith('Published score join:')]
        assert len(joined) == 1, identifier
        join_cell, join_text = joined[0]
        match = re.fullmatch(r'Published score join: (\d+) variants; missing scores: (\d+)\s*', join_text)
        variants, missing = map(int, match.groups())
        dataset = current['dataset_split']
        assert dataset['variants'] == variants == 273135
        assert dataset['missing_released_scores'] == missing == 0
        assert dataset['restored_variants'] == variants - dataset['historical_supporting_variants'] == 1934
        assert dataset['assays'] == 73 and dataset['proteins'] == 64
        assert evidence['cohort_output_cell'] == join_cell
        panel_text = [text for _, text in outputs if text.startswith('Variants before released-score join:')]
        assert len(panel_text) == 1 and '273135 Assays: 73 Proteins: 64' in panel_text[0]
        split_text = next(text for index, text in outputs
                          if index == join_cell and 'variants  assays  proteins' in text)
        splits = {name: {'variants': int(n), 'assays': int(a), 'proteins': int(p)}
                  for name, n, a, p in re.findall(
                      r'^(discovery|confirmation)\s+(\d+)\s+(\d+)\s+(\d+)', split_text, re.M)}
        assert splits == dataset['splits_before_axis_eligibility'], identifier
        assert sum(row['variants'] for row in splits.values()) == variants
        section = next(index for index, cell in enumerate(notebook['cells'])
                       if cell['cell_type'] == 'markdown' and ''.join(cell['source']).startswith('## 6'))
        results = [text.strip() for index, text in outputs if index > section and text.strip()]
        reported = current['curve']['reported_result']
        if identifier.endswith('test-02'):
            controls = next(text for _, text in outputs
                            if 'Excluding stability' in text and 'n_assays' in text and 'rho' in text)
            expected = [{'subset': name, 'assays': int(n), 'rho': float(rho), 'p': float(p)}
                        for name, n, rho, p in re.findall(
                            rf'^\d+\s+(All|Excluding stability|Stability only|Discovery|Confirmation)\s+(\d+)\s+({NUMBER})\s+({NUMBER})',
                            controls, re.M)]
            assert len(expected) == 5 and expected == reported['control_associations'], identifier
            assert reported['reported_decimal_places'] == 6
        else:
            conclusion = next(text for text in results if text.startswith('**'))
            match = re.search(
                rf'effect is ({NUMBER}) \(95% interval ({NUMBER}) to ({NUMBER}); (\d+) assays\)\. The confirmation effect is ({NUMBER})\.',
                conclusion)
            estimate, low, high, assays, confirmation = match.groups()
            assert reported['estimate'] == float(estimate), identifier
            assert reported['confidence_interval_95'] == [float(low), float(high)], identifier
            assert reported['eligible_assays'] == int(assays), identifier
            assert reported['confirmation_estimate'] == float(confirmation), identifier
            assert reported['reported_decimal_places'] == 3
            expected = []
            for text in results:
                match = re.match(
                    rf'(AM minus BLOSUM|AM minus PSSM): ({NUMBER}) \(95% interval ({NUMBER}) to ({NUMBER})\); (.+)\.', text)
                if match:
                    comparison, value, low, high, explanation = match.groups()
                    expected.append({'comparison': comparison, 'estimate': float(value),
                                     'confidence_interval_95': [float(low), float(high)],
                                     'interpretation': explanation, 'reported_decimal_places': 3})
            assert len(expected) == 2 and expected == current['insight']['comparator_contrasts'], identifier
        assert current['model_evaluation']['fresh_target_inference'] is False
        assert current['model_evaluation']['target_fine_tuning'] is False
        checked.append(identifier)
    assert len(checked) == 6
    return checked


if __name__ == '__main__':
    print(json.dumps({'current_metadata_checked': verify(),
                      'scientific_workflows_rerun': 0}, indent=2))
