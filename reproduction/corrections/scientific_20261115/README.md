# Scientific calculation corrections — November 15, 2026

The calculation issues found in the individual notebook review are corrected in **21 notebooks**. Ten STATE primary notebooks were executed in full. The affected calculation and interpretation cells were executed in eleven other notebooks; their remaining code cells and saved outputs are unchanged. This is a correction of retained-data analyses, not new model inference or new external validation.

| Analyses | Correction | Result after correction |
|---|---|---|
| STATE primary tests 05, 09, 10, 13–19 | Removed redundant subset indicators while retaining context and representation controls; clustered uncertainty by canonical gene. | The response-adjusted support coefficient remains positive: 0.028448, 95% CI [0.022269, 0.034627], from 6,640 rows and 1,391 genes. The GO molecular-function adjusted interval includes zero. |
| STATE Kimi r1 tests 01–04 | Replaced the invalid pooled embedding statistic and pooled independence assumptions with joint gene-cluster resampling. | Pooled embedding correlation 0.504528 [0.473704, 0.533788]; seen-minus-unseen contrast 0.117729 [0.096873, 0.138288], using 1,949 gene clusters. No pooled independence-based p-value is reported. |
| STATE Opus r2 test 05 | Used categorical context indicators, gene-cluster uncertainty, and deterministic SHA-256 split membership. | Adjusted partial rank correlations remain positive: HVG 0.147379 [0.113562, 0.180705]; SE 0.126895 [0.095797, 0.159755]. The 956/955-gene partition is a retrospective sensitivity check, not prospective confirmation. |
| STATE Codex r1 test 04 | Corrected the first graph's x-axis and title; rebuilt its points and uncertainty from the retained individual records. | The graph measures baseline S-phase-score standard deviation. All values agree with the earlier table at its displayed precision. |
| AlphaMissense primary tests 03–07 | Resampled proteins with their assays together; removed degenerate intervals and unsupported endpoint decisions. | The depth contrast remains +0.523308 but has one assay/one protein: no between-protein CI. Occupancy remains +0.214838 [0.156994, 0.272468] across 44 assays/40 proteins; high-depth occupancy remains +0.151933 [0.028273, 0.283765] across 19/17. |

All intervals in the table are 95% intervals. They describe the stated retained cohorts and resampling units. No cohort, endpoint or feature bin was changed to obtain a positive result. The AlphaMissense retained-profile reconstruction produces a small PSSM reference difference (maximum weighted curve change about 0.0000073); its report documents this rather than claiming byte-identical recovery of the old intermediate files.

## Code, inputs and execution

- [Updated notebook catalog](../../inline/INDEX.md), with separate labels for original execution, full reruns and affected-calculation reruns.
- [Per-notebook correction records](integrated.json), linking the executed cells, input hashes, outputs and preserved original execution receipts.
- STATE primary: [frozen plan](state_primary/PLAN.md), [independent regression checks](state_primary/regression-verification.json), [verification code](state_primary/verify_regressions.py), and [outputs](state_primary/outputs/).
- STATE Kimi/Opus: [registration and input identities](state_kimi_opus/registration.json), [numerical checks](state_kimi_opus/real_data_checks.json), and [portable input restoration](state_kimi_opus/restore_inputs.py).
- STATE plot: [rerun code](state_plot/rerun_plot.py), [recomputed curve](state_plot/outputs/corrected_curve.csv), and [numerical comparison](state_plot/outputs/numerical_check.json).
- AlphaMissense: [methods, results and reproduction commands](alphamissense/README.md), [verification](alphamissense/verification.json), and [before/after comparisons](alphamissense/verification_tables/).

Inputs are either existing public repository payloads or compressed copies of those retained inputs included with the correction. They require no private GCP access. Previous notebooks and receipts are preserved under `records/`; each current receipt states its actual execution scope and host. Source, output, input and rendered-page hashes are checked separately from scientific interpretation.

## Verification

From the repository root, in the notebook environment with NumPy, pandas, SciPy, statsmodels, nbformat and nbconvert installed:

```bash
python reproduction/validate.py
python reproduction/test_scientific_revision.py
python reproduction/corrections/scientific_20261115/state_primary/verify_regressions.py
python reproduction/corrections/scientific_20261115/alphamissense/verify_correction.py
```

The STATE primary regression checks compare coefficients and clustered intervals against an independent implementation, assert full-rank controls, and test that repeating gene records does not create independent information. Kimi/Opus checks compare weighted bootstrap calculations against explicit resampled rows. AlphaMissense checks cover one-protein guards, whole-protein resampling, preserved counts and unchanged endpoint estimates. The plot was independently recomputed from the 17,040-row retained source, using its 4,020 confirmation records.

These changes resolve the identified calculation defects. They do not supply missing historical records, change the ESMFold v1 analysis into ESMFold2, or turn internal/tile-level comparisons into independent patient/site confirmation. Those boundaries remain explicit in the relevant notebooks.

The [final independent integration check](../../review_20261115/scientific-final-integration-independent-check.json) verifies all 21 corrections and confirms that the other 122 notebook files remain unchanged. The [independent AlphaMissense check](../../review_20261115/alphamissense-science-independent-check.json) recalculates the assay statistics and corrected intervals from individual variants. [Browser checks](browser-checks.json) cover the 21 revised pages.
