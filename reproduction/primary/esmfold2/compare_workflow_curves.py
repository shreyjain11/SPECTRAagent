"""Compare the integrated original-analysis route with retained historical curves.

Run only on explicitly staged retained-data validation outputs, never on a new
model run whose predictions are allowed to differ. No inference or downloads.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / 'original_runs'
SINGLE = 'esmfold2_single_controller_final_run'
BEYOND = 'esmfold2_beyond_evolutionary_support_final_run'
GEOMETRY = 'esmfold2_new_axes_after_scaling_external_20260531T193531Z'
GLOBAL = 'esmfold2_global_hypothesis_audit_20260602/analysis_outputs'
ENVELOPE = 'esmfold2_envelope_fusion_axis_confirmation_20260602/analysis_outputs'

# Every primary axis has at least one direct numerical comparison. Additional
# controls/screens are exercised by validate_original_workflow.py.
PAIRS = [
    (1, 'spectral_performance_curve.csv', f'{SINGLE}/spectral_performance_curve.csv'),
    (2, 'spectral_performance_curve.csv', f'{SINGLE}/spectral_performance_curve.csv'),
    (3, 'spectral_curves_all_axes.csv', f'{BEYOND}/spectral_curves_all_axes.csv'),
    (3, 'followup_axis_curves.csv', f'{BEYOND}/followup_axis_curves.csv'),
    (3, 'flexible107_curves.csv', 'esmfold2_external_flexible_axis_expanded_20260601T170049Z/expanded_external_spc_by_level.csv'),
    (4, 'charge97_curves.csv', 'esmfold2_charge_axis_fresh_rcsb_confirmation_20260601T205925Z/analysis_outputs/charge_confirmation_level_curves.csv'),
    (4, 'frozen_charge_axis_curves.csv', f'{GEOMETRY}/frozen_charge_axis_curves.csv'),
    (4, 'frozen_charge_hydropathy_axis_curves.csv', f'{GEOMETRY}/frozen_charge_hydropathy_axis_curves.csv'),
    (5, 'acidic78_curves.csv', 'esmfold2_all_evidence_confirmation_loop_20260601T215426Z/analysis_outputs/acidic_window_confirmation_level_curves.csv'),
    (6, 'cysteine95_curves.csv', 'esmfold2_all_scored_evidence_loop_20260601T230100Z/analysis_outputs/cys_confirmation_level_curves.csv'),
    (7, 'all_evaluations_curves.csv', f'{GLOBAL}/global_hypothesis_level_curves_all_evaluations.csv'),
    (7, 'primary_sequence_curves.csv', f'{GLOBAL}/global_hypothesis_level_curves_primary_sequence.csv'),
    (8, 'all_evaluations_curves.csv', f'{GLOBAL}/global_hypothesis_level_curves_all_evaluations.csv'),
    (8, 'primary_sequence_curves.csv', f'{GLOBAL}/global_hypothesis_level_curves_primary_sequence.csv'),
    (9, 'frozen_reference_topology_axis_curves.csv', f'{GEOMETRY}/frozen_reference_topology_axis_curves.csv'),
    (10, 'viral36_curves.csv', 'esmfold2_viral_disulfide_axis_pilot_20260602/analysis_outputs/viral_disulfide_pilot_level_curves.csv'),
    (11, 'envelope38_curves.csv', f'{ENVELOPE}/envelope_fusion_confirmation_level_curves.csv'),
    (12, 'envelope38_curves.csv', f'{ENVELOPE}/envelope_fusion_confirmation_level_curves.csv'),
    (12, 'surface45_curves.csv', f'{ENVELOPE}/surface_lowhelical_confirmation_level_curves.csv'),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('workspace', type=Path)
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    receipt = json.loads((workspace / 'feature_reconstruction_report.json').read_text())
    if receipt['mode'] != 'retained_original_data_integration_fixture':
        raise ValueError('This equality check is only for retained-data integration fixtures.')
    checks = []
    for axis, filename, original in PAIRS:
        generated_path = workspace / 'analysis' / f'axis-{axis:02}' / filename
        original_path = RUNS / original
        record = {'axis': axis, 'generated': str(generated_path),
                  'original': str(original_path.relative_to(ROOT))}
        try:
            generated = pd.read_csv(generated_path)
            retained = pd.read_csv(original_path)
            generated = generated.loc[:, retained.columns]
            keys = [c for c in retained if not pd.api.types.is_numeric_dtype(retained[c])]
            keys += [c for c in retained if c not in keys and (
                c == 'level' or c == 'axis_level' or c.endswith('_level'))]
            if keys:
                generated = generated.sort_values(keys, kind='stable')
                retained = retained.sort_values(keys, kind='stable')
            generated = generated.reset_index(drop=True)
            retained = retained.reset_index(drop=True)
            pd.testing.assert_frame_equal(generated, retained, check_dtype=False,
                                          check_exact=False, atol=1e-10, rtol=1e-10)
            numeric = retained.select_dtypes(include='number').columns
            difference = (generated[numeric] - retained[numeric]).abs().to_numpy()
            maximum = float(np.nanmax(difference)) if difference.size else 0.0
            record.update(status='passed', rows=len(retained), columns=len(retained.columns),
                          maximum_absolute_numeric_difference=maximum,
                          generated_sha256=digest(generated_path), original_sha256=digest(original_path))
        except Exception as error:
            record.update(status='failed', error=str(error))
        checks.append(record)
    report = {'scope': 'Direct numerical comparison of integrated original-analysis outputs using retained original inputs and model measurements',
              'full_raw_to_model_run_executed': False, 'inference_executed': False,
              'absolute_tolerance': 1e-10, 'relative_tolerance': 1e-10,
              'axes_checked': sorted(set(row['axis'] for row in checks)),
              'all_passed': all(row['status'] == 'passed' for row in checks), 'tables': checks}
    (ROOT / 'CURVE_REPLAY_VALIDATION.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'all_passed': report['all_passed'], 'tables': len(checks),
                      'rows': sum(row.get('rows', 0) for row in checks),
                      'failures': [row for row in checks if row['status'] != 'passed']}, indent=2))
    if not report['all_passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
