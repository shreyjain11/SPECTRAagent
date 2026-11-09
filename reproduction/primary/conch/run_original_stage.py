"""Run unchanged recovered scripts with pinned local image sources.

Only input locations and identity guards are adapted; all feature, selection,
prompt, scoring and analysis functions are the recovered original functions.
"""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'originals/scripts'))


def build_features(parquet_dir, reference, output):
    import pandas as pd
    import build_crc_candidate_table as original
    from freeze_axes import feature_columns
    crc = original.build_crc_features(parquet_dir)
    ref = pd.read_csv(reference)
    assert len(crc) == 7180 and len(ref) == 1800
    assert crc.sample_id.is_unique and ref.sample_id.is_unique
    # Outcomes are not read. Check exact original images and order before scoring.
    old = pd.read_csv(ROOT / 'data/discovery.csv', usecols=['sample_id', 'label', 'image_md5'])
    for col in ['sample_id', 'label', 'image_md5']:
        assert crc[col].tolist() == old[col].tolist(), f'Original CRC identity mismatch: {col}'
    combined = pd.concat([crc, ref], ignore_index=True)
    assert len(feature_columns(combined)) == 67
    output.mkdir(parents=True, exist_ok=True)
    crc.to_csv(output / 'crc_val_candidate_features.csv', index=False)
    ref.to_csv(output / 'nct_reference_features.csv', index=False)
    combined.to_csv(output / 'candidate_features.csv', index=False)
    (output / 'dataset_diagnostics.json').write_text(json.dumps({
        'crc_val_rows': len(crc), 'nct_reference_rows': len(ref),
        'original_image_md5_and_order_matches': len(crc), 'feature_columns': 67,
        'target_predictions_used_for_feature_construction': False,
    }, indent=2))


def configure_module(name, data_root):
    import build_crc_candidate_table as features
    features.HF_BASE = str(data_root.resolve()) + '/'
    # These constants are imported by value, so redirect both defining modules
    # before importing either panel builder or scorer.
    if 'tum_' in name:
        import build_tum_confirmation_panel as confirmation
        confirmation.HF_BASE = features.HF_BASE
    module = importlib.import_module(name)
    if hasattr(module, 'HF_BASE'):
        module.HF_BASE = features.HF_BASE
    return module


def guard_panel_stream(module):
    import numpy as np
    original_stream = module.stream_selected

    def checked(panel):
        seen = set()
        for row, image in original_stream(panel):
            assert row.sample_id not in seen, row.sample_id
            seen.add(row.sample_id)
            # Original panel MD5 uses decoded, 224x224 RGB pixels.
            rgb = image.convert('RGB')
            if rgb.size != (224, 224):
                from PIL import Image
                rgb = rgb.resize((224, 224), Image.Resampling.BICUBIC)
            assert hashlib.md5(np.asarray(rgb, dtype=np.uint8).tobytes()).hexdigest() == row.image_md5, row.sample_id
            yield row, image
        assert len(seen) == len(panel)
    module.stream_selected = checked


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--module', required=True)
    parser.add_argument('--data-root', type=Path, required=True)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--output', type=Path)
    args, original_args = parser.parse_known_args()
    if original_args[:1] == ['--']:
        original_args = original_args[1:]
    if args.module == 'build_features':
        build_features(args.data_root / 'data', args.reference, args.output)
        return
    module = configure_module(args.module, args.data_root)
    if args.module in ['score_tum_confirmation', 'score_tum_panel_generic']:
        guard_panel_stream(module)
    sys.argv = [str(ROOT / 'originals/scripts' / (args.module + '.py')), *original_args]
    result=module.main()
    if args.module=='freeze_axes':
        # The original script has one historical absolute path in descriptive
        # ledger metadata; no scientific value or source file is altered.
        ledger=Path('axis_ledger.json')
        if ledger.exists():
            value=json.loads(ledger.read_text())
            value['paper_reference']='source/CONCH/README.md'
            ledger.write_text(json.dumps(value,indent=2))
    raise SystemExit(result)


if __name__ == '__main__':
    main()
