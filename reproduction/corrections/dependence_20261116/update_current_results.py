"""Update current JSON summaries from the executed dependence-correction tables."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def evidence(path):
    return {'path': str(path.relative_to(ROOT)),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    source = HERE / 'alphamissense/current_results.json'
    results = read(source)
    expected = {f'am-opus-r{rep}/test-{test:02d}' for rep in (1, 2) for test in (1, 2, 3)}
    assert set(results) == expected
    for identifier in sorted(expected):
        path = ROOT / 'analyses' / (identifier + '.json')
        record = read(path)
        current = record['current_inline_analysis']
        summary = results[identifier]
        current['evidence']['statistical_result'] = evidence(source)
        current['evidence']['verification_method'] = (
            'Full notebook reexecution from pinned public inputs; current numerical '
            'metadata is bound to the exported correction results and execution record.')
        current['curve'] = {key: summary[key] for key in
                            ['reported_result', 'aggregation_and_uncertainty']}
        for key in ['interpretation', 'comparator_contrasts']:
            current['insight'][key] = summary[key]
        if 'adjusted_controls' in summary:
            current['insight']['adjusted_controls'] = summary['adjusted_controls']
        else:
            current['insight'].pop('adjusted_controls', None)
        current['limitations'] = [text for text in current['limitations']
            if not text.startswith(('This metadata was extracted', 'The notebook association rule',
                                    'Protein-cluster uncertainty is conditional'))]
        current['limitations'].insert(0,
            'Protein-cluster uncertainty is conditional on this retained assay panel. '
            'The intervals are pointwise and do not correct for multiple exploratory comparisons.')
        write(path, record)

    identifier = 'state-featured/test-03'
    path = ROOT / 'analyses' / (identifier + '.json')
    record = read(path)
    current = record['current_inline_analysis']
    table = HERE / 'state/before-after-contrasts.csv'
    rows = list(csv.DictReader(table.open()))
    contrasts = []
    for row in rows:
        contrasts.append({
            'subset': row['subset'], 'representation': row['representation'],
            'high_level': row['high_level_gene_bootstrap'],
            'low_level': row['low_level_gene_bootstrap'],
            'estimate': float(row['gap_high_minus_low_gene_bootstrap']),
            'confidence_interval_95': [float(row['ci_low_gene_bootstrap']),
                                       float(row['ci_high_gene_bootstrap'])],
            'gene_clusters': int(row['gene_clusters']),
            'low_rows': int(row['low_n_gene_bootstrap']),
            'high_rows': int(row['high_n_gene_bootstrap']),
            'populated_annotated_levels': int(row['populated_annotated_levels'])})
    current['curve'] = {
        'metric': 'Row-weighted mean overlap@N, L2 minus L1',
        'aggregation_and_uncertainty': 'Joint canonical-gene bootstrap across both '
            'endpoints and observed contexts; 2,000 draws, seed 7, 95% percentile intervals.',
        'contrasts': contrasts, 'evidence': evidence(table)}
    current['insight'] = {
        'interpretation': 'Higher annotated similarity is associated with higher '
            'overlap@N in the two populated annotated levels for both representations '
            'and context subsets. This is a bounded two-level comparison, not a '
            'validated three-level curve or full protocol acceptance.',
        'limitations': ['Unannotated L0 is descriptive and does not supply a third similarity level.',
            'Inference is conditional on the observed contexts and reconstructed reference membership.',
            'Released scores were reused; this correction did not run fresh model inference '
            'or establish independent external confirmation.']}
    write(path, record)
    print('Updated seven current result summaries from executed correction outputs.')


if __name__ == '__main__':
    main()
