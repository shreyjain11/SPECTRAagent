# CONCH SPECTRA Generalizability Audit

## Finding

A claim-valid but localized SPECTRA finding is supported for CONCH zero-shot CRC ROI classification: true TUM / colorectal adenocarcinoma epithelium recall degrades in the low-similarity tail of a prospective tissue-fraction axis. The axis is not target confidence or error based; it is computed from tissue, white, dark, and high-saturation pixel fractions relative to a class-balanced NCT-CRC-HE-100K reference.

Claim boundary: public CRC 224x224 H&E ROI tiles scored with the CONCH CRC prompt ensemble. This is a TUM-class, acquisition/content-quality boundary, not a broad all-class, WSI, hospital/site, non-CRC, or medical deployment claim. Confirmation is fresh relative to CRC-VAL discovery but comes from the same public Kather/NCT source family, not an independent site cohort.

## Data And Leakage Controls

- Model: `conch_ViT-B-16` from `MahmoodLab/conch`, source commit `141cc09c7d4ff33d8eda562bd75169b457f71a62`; checkpoint cached under `model_cache/` with size 802,235,437 bytes.
- Discovery/evaluation pool: all 7,180 CRC-VAL-HE-7K images from the public NCT-CRC-HE mirror. Exact MD5 duplicates: 0; dHash64 duplicates: 0.
- Prospective reference: 1,800 streamed NCT-CRC-HE-100K images, 200 per class, used only for fixed feature axes and baselines.
- Confirmation pool: 1,800 fresh NCT-CRC-HE-100K-NONORM TUM images, 600 from each of three public TUM shards, frozen into six equal-count levels before CONCH scoring.

## Key Numbers

Overall CONCH on CRC-VAL: accuracy 0.793, balanced accuracy 0.785, macro F1 0.769. Fixed NCT-feature baselines were lower: centroid balanced accuracy 0.602, logistic balanced accuracy 0.619.

CRC-VAL TUM discovery on the frozen tissue-fraction axis, levels 1 to 6 as similarity decreases: TUM recall [0.779, 0.652, 0.63, 0.574, 0.39, 0.114]. The lowest-similarity CRC-VAL TUM level had much more white/background-like area: mean tissue fraction 0.605 and white fraction 0.395, versus 0.969 tissue and 0.030 white in level 1.

NONORM TUM confirmation, 300 images per level: CONCH TUM recall [0.903, 0.93, 0.93, 0.883, 0.697, 0.73]. Densified deciles preserved the threshold shape: deciles 1-7 were mostly 0.85-0.94 recall, while deciles 8-10 were [0.678, 0.733, 0.722].

Fixed baselines on the same confirmation levels were substantially weaker and also degraded with low similarity. Centroid TUM recall by level: [0.53, 0.223, 0.27, 0.197, 0.057, 0.0]; logistic TUM recall by level: [0.353, 0.153, 0.14, 0.023, 0.0, 0.0].

## Nonprimary Axes

The broader NCT color/texture proximity axis was split-valid but not claim-closing. Its balanced accuracy fell in the low-similarity tail, but raw accuracy rose because low-similarity levels were dominated by easy ADI/BACK/DEB patches. Class-adjusted and stable-class checks did not support using it as the primary all-class generalizability claim.

## Artifacts

- `spectra_loop_state.json`
- `axis_ledger.json`
- `commands_run.json`
- `spectra_ready_dataset/`
- `target_model_results.csv`
- `artifacts/spc_analysis/spc_summary.json`
- `artifacts/tum_confirmation/analysis.json`
- `final_report.md`
