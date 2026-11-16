# Dependence corrections — November 16, 2026

Seven notebooks had uncertainty calculations that treated related observations as independent. All seven were corrected and executed in full: six AlphaMissense Opus notebooks (66 code cells) and STATE primary test 03 (13 code cells). These calculations reuse public inputs and released model scores. They do not involve fresh model inference or audit-specific fine-tuning.

## What changed and what the results show

- **AlphaMissense Opus:** resample whole proteins with all their assays, preserving the original assay-weighted estimates. Paired tests use protein-block sign flips with their assumption stated. Depth intervals rerank each resample. Adjusted regressions use protein-clustered covariance and count the absorbed assay intercepts. The cohort remains 273,135 variants, 73 assays and 64 proteins, including the 1,934 restored variants.
- **STATE primary test 03:** resample canonical genes jointly across endpoints and contexts, retaining all rows of each sampled gene. The conclusion now describes the two populated annotated levels. Unannotated L0 is not a third informative level.

| Analysis | Corrected result |
|---|---|
| AlphaMissense constraint, positional coverage, residue confidence and alignment support | Pooled residue contrasts remain positive within the measured panel. None of the four pooled AlphaMissense-minus-PSSM intervals excludes zero. The r1 positional-coverage comparison with BLOSUM also includes zero. |
| AlphaMissense whole-protein depth | Inconclusive: Spearman rho 0.04604, 95% protein-bootstrap interval −0.23126 to 0.31269. The two notebooks share this calculation; they are not independent corroborations. |
| AlphaMissense adjusted r2 controls | Coverage intervals include zero; residue-confidence intervals remain positive. These are conditional associations, not causal mechanisms. |
| STATE annotated L2 minus L1, Jurkat/RPE1 | HVG 0.096027 [0.073875, 0.119098]; SE 0.084276 [0.062477, 0.105951], with 1,222 genes per representation. This supports a two-level association in the fixed panel, not a three-level curve or full protocol completion. |

Intervals are nominal 95% intervals conditional on the retained panels and fixed axis definitions. Internal partitions do not establish independent external confirmation. See the [AlphaMissense methods/results](alphamissense/README.md) and [STATE before/after comparison](state/README.md) for exact estimates, counts, assumptions and reproduction details.

## Verification

An independent implementation checked 87 AlphaMissense curve rows, 160 paired contrasts, 10 depth intervals and four displayed regression fits (two unique designs). It also reproduced all 8,000 STATE bootstrap draws by expanding the sampled gene rows. [Method review](independent/method-review.md), [numerical checks](independent/), and [integration check](independent/final-integration-review.json) record the scope.

The STATE individual records, point estimates, levels, curve tables and plot match the original-code replay exactly. AlphaMissense original aggregation on current records preserves point estimates to numerical precision. Two complete unmodified-original replays also match their corrected reconstructions exactly. Tiny differences from historical displayed values remain in two AlphaMissense notebooks (maximum 0.0000373); they occur without the uncertainty repair, and their exact original-platform cause is unresolved. The [three-way comparison](alphamissense/three-way-verification.json) documents this boundary.

Current notebooks, HTML, analysis JSON and execution receipts agree. [Original notebooks and receipts](records/) remain preserved, and the [integration index](integrated.json) links each correction. All custom scientific analysis code is inline in the notebooks. The scripts here apply, execute, verify or register the repair; the notebooks do not import them as hidden analysis code.

From the repository root:

```sh
python reproduction/validate.py
python reproduction/test_scientific_revision.py
python reproduction/corrections/alphamissense/verify_current_records.py
python reproduction/corrections/dependence_20261116/independent/test_current_records_revision.py
```

All 143 entries receive integrity checks; only the seven notebooks above were newly executed in this correction. The other 136 notebook files are unchanged from `01461707b4c37faba205b053c4c623a58cbd0cb1`. This resolves the specified dependence defects, not every limitation of the historical audits. The [previous 21 corrections](../scientific_20261115/README.md), ESMFold v1 limitation, one-protein descriptive comparison, and patient/site validation boundaries remain explicit.
