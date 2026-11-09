# CONCH TUM Tissue/Stain-Fraction SPC Expansion

## Status

This expansion strengthens the prior localized finding. The same prospective axis was kept frozen before target scoring: Euclidean distance in tissue, white, dark, and high-saturation pixel fractions from the class-balanced NCT reference median, with higher numbered levels meaning lower similarity.

The expanded panel used 4,000 unused NCT-CRC-HE-100K-NONORM TUM images, 400 per frozen level. It excluded all 1,800 previously scored confirmation rows by stream key and exact decoded-image MD5. Internal exact MD5 duplicates were 0, exact overlap with the previous panel was 0, and dHash64 overlap with the previous panel was 0. Mean measured similarity decreased across all 10 levels.

Validity decision: `valid` for the bounded public CRC ROI TUM low-similarity tail boundary; `weak` for independent-site or deployment generalization because all confirmation evidence is still from the public Kather/NCT source family.

## Expanded Curve

| Level | n | Axis Mean | CONCH TUM Recall | 95% CI | Centroid | Logistic | Dark Mean | Sat-High Mean |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 400 | -0.032 | 0.875 | [0.839, 0.904] | 0.660 | 0.378 | 0.004 | 0.063 |
| 2 | 400 | -0.052 | 0.950 | [0.924, 0.967] | 0.330 | 0.255 | 0.003 | 0.043 |
| 3 | 400 | -0.065 | 0.943 | [0.915, 0.961] | 0.150 | 0.107 | 0.002 | 0.027 |
| 4 | 400 | -0.079 | 0.927 | [0.898, 0.949] | 0.247 | 0.172 | 0.003 | 0.047 |
| 5 | 400 | -0.107 | 0.912 | [0.881, 0.936] | 0.290 | 0.165 | 0.006 | 0.065 |
| 6 | 400 | -0.153 | 0.890 | [0.856, 0.917] | 0.228 | 0.060 | 0.010 | 0.069 |
| 7 | 400 | -0.245 | 0.830 | [0.790, 0.864] | 0.158 | 0.000 | 0.021 | 0.099 |
| 8 | 400 | -0.434 | 0.640 | [0.592, 0.686] | 0.075 | 0.000 | 0.104 | 0.320 |
| 9 | 400 | -0.640 | 0.700 | [0.653, 0.743] | 0.007 | 0.000 | 0.245 | 0.591 |
| 10 | 400 | -0.847 | 0.703 | [0.656, 0.745] | 0.000 | 0.000 | 0.388 | 0.799 |

## Main Contrast

Levels 1-7 stayed high overall: 2531/2800 = 0.904 TUM recall, 95% CI [0.892, 0.914].

Levels 8-10 formed the low-similarity tail: 817/1200 = 0.681 TUM recall, 95% CI [0.654, 0.707].

Difference, levels 1-7 minus 8-10: 0.223, 95% CI [0.195, 0.252], two-sided normal p ~= 1.30e-68.

The curve is threshold-shaped rather than strictly monotone: levels 8-10 are consistently degraded, but level 9 and 10 rebound slightly relative to level 8. Spearman level-vs-recall over the 10 frozen bins is -0.770.

## Baseline Comparison

CONCH overall TUM recall on the expansion panel was 0.837. Fixed feature baselines were much lower: centroid 0.214, logistic 0.114. The baselines also degrade strongly in the low-similarity tail, which supports the axis as a real prospective image-distribution shift rather than a CONCH-confidence artifact.

## Interpretation

The low-similarity tail is not simply low tissue area. In the expanded panel it is mainly a dark/high-saturation stain tail: mean dark fraction rises from 0.004 at level 1 to 0.388 at level 10, and high-saturation fraction rises from 0.063 to 0.799.

Exploratory failure characterization, not an axis definition: in levels 8-10, non-TUM predictions were mostly STR, MUC, DEB, and BACK. This was computed after target scoring and should not be used as confirmatory split logic.

## Relation To Previous Confirmation

The earlier six-level confirmation had TUM recall [0.903, 0.930, 0.930, 0.883, 0.697, 0.730]. The expanded 10-level panel reproduces the same low-tail shape with more examples per level: levels 8-10 were [0.640, 0.700, 0.703].

## Artifacts

- `spectra_ready_dataset/tum_expansion_panel.csv`
- `artifacts/tum_expansion/panel_diagnostics.json`
- `artifacts/tum_expansion/target_model_results_tum_expansion.csv`
- `artifacts/tum_expansion/analysis.json`
- `artifacts/tum_expansion/expanded_metrics.json`
- `artifacts/tum_expansion/scored_tum_expansion_with_baselines.csv`
