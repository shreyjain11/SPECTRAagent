# AlphaMissense Opus: protein-aware uncertainty

All six Opus notebooks were executed in full from the four checksum-pinned public inputs. The actual local environment was Python 3.13.2, NumPy 2.1.2, pandas 2.3.1 and SciPy 1.16.0, with pyhmmer 0.12.1 and Biopython 1.85; see `environment.json`. It is not claimed to match the historical Broad environment. The scored cohort remains 273,135 variants in 73 assays of 64 proteins. No model inference or audit-specific fine-tuning was performed. The original notebooks and execution receipts are retained under `before/`; the frozen repair plan and its timestamp/hash are in `PLAN.md` and `frozen-plan.json`.

## What changed

Curve and paired-contrast point estimates remain assay-weighted. Bootstrap draws now select entire protein accessions and include every eligible assay of each selected protein. The analysis does not replace these estimates with equally weighted protein means. Each table reports both assay and protein counts.

The paired tests now use a protein-block sign-flip test. This requires joint sign symmetry of the assay contrasts within each protein and independence between protein blocks. Its null differs from the removed independent-assay Wilcoxon test; their p-values are not directly interchangeable. Tests enumerate all signs for at most 16 proteins and otherwise use 50,000 draws with a finite-simulation correction.

The depth screens retain the original across-assay Spearman coefficients. Their intervals resample entire proteins and rerank every expanded draw. The independent-assay analytic p-values are removed. No bootstrap-tail fraction is presented as a p-value.

The r2 adjusted controls retain the same within-assay OLS coefficients and bins. Their covariance now clusters by protein. The CR1 correction counts the absorbed assay intercepts as fitted parameters, and intervals/tests use t(G−1), with G the protein count. The full-rank condition is checked explicitly.

All bootstrap intervals use 10,000 draws. With fewer than two proteins, population intervals/tests are unavailable; fewer than ten proteins is flagged as limited. The displayed primary comparisons have at least 14 confirmation proteins and 24 pooled proteins. Intervals and tests remain nominal and are not adjusted for the exploratory comparisons. Protein-separated partitions within the fixed panel do not establish independent historical axis selection or external confirmation.

## Current numerical results

| Notebook | Pooled AlphaMissense contrast or depth association | 95% protein-aware interval | Assays / proteins |
|---|---:|---:|---:|
| r1/test-01, constraint | 0.16517 | 0.12199 to 0.20809 | 70 / 62 |
| r1/test-02, depth Spearman | 0.04604 | −0.23126 to 0.31269 | 73 / 64 |
| r1/test-03, positional coverage | 0.09841 | 0.04172 to 0.15083 | 71 / 63 |
| r2/test-01, residue confidence | 0.32307 | 0.23252 to 0.40327 | 27 / 24 |
| r2/test-02, depth Spearman | 0.04604 | −0.23126 to 0.31269 | 73 / 64 |
| r2/test-03, alignment support | 0.21082 | 0.14917 to 0.27147 | 43 / 38 |

The positive residue contrasts also have positive intervals in their displayed confirmation partitions. None of the four pooled AlphaMissense-minus-PSSM contrast intervals establishes a positive difference. The r1 positional-coverage comparison with BLOSUM also includes zero. Whole-protein depth remains inconclusive, including after removing stability assays: rho 0.15496, interval −0.15017 to 0.45466, 59 assays / 50 proteins.

In the two r2 control designs, the adjusted coverage intervals include zero (−0.03844 to 0.17103; −0.13835 to 0.27677), while the pLDDT intervals remain positive (0.00209 to 0.00695; 0.00200 to 0.00725). These conditional associations do not establish a separate causal mechanism.

Exact values, cohort counts, comparator contrasts and adjusted coefficients are exported directly from notebook calculations in `current_results.json`, with the per-notebook originals in `outputs/*/CURRENT_RESULTS.json`. `build_current_results.py` adds the interpretation/method fields without recalculating scientific values.

## Verification and numerical replay boundary

An independent reviewer checked all 87 curve rows, 160 paired-contrast rows, 10 depth-subset intervals and four displayed adjusted fits (two distinct designs repeated across the r2 notebooks). Explicit full assay-dummy regressions agree with the corrected clustered standard errors to at most 3.5×10⁻¹⁵. See [independent checks](../independent/) for the calculations. Helper fixtures check unequal assay counts per protein, whole-block resampling, exact sign flips, degenerate one-protein inference and depth reranking.

Replaying the original aggregation on the current generated assay records gives the corrected point estimates to at most 1.12×10⁻¹⁶, with identical eligibility counts. Thus the uncertainty correction itself does not change the statistical point estimate on a fixed set of inputs.

The full current raw reconstruction is not byte-identical to every historical displayed number. In r1/test-01 the largest difference among displayed curve/contrast means is 3.7283×10⁻⁵; in r1/test-03 it is 3.3175×10⁻⁶. The other four notebooks agree to the original six-decimal display precision. Historical full-precision per-assay output files from the original inline execution were not available. `point-estimate-verification.json` and the `before-after-*.csv` files disclose these differences rather than treating them as exact historical agreement.

The independently rebuilt r1 residue profiles match each other and the available older public profiles exactly. Numerical sensitivity of entropy ordering and PSSM ties is demonstrated in diagnostic files, but those older profiles do not identify the exact cause of the later historical display differences. No entropy calculation, PSSM formula, bin definition, threshold or membership was changed to force agreement. Two exact unmodified original notebooks were also executed in full under the same current environment. Their assay-level score tables, processing counts and score-position mappings match the corrected executions exactly; all 48 curve means and 100 paired-contrast means match exactly as well. Thus the historical display differences also occur without the dependence repair. These completed replays and three-way comparisons are recorded under `original-method-replays/` and `three-way-verification.json`. The exact original-platform cause remains unidentified.

`registration.json` supplies the full-execution records for repository integration. Public source URLs and exact consumed input hashes are in `public-source-inputs.json`; large raw archives are not duplicated in this correction package. All custom analysis code remains inline in the six notebooks.
