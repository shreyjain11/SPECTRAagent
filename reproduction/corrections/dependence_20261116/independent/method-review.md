# Independent methodological review: seven dependence corrections

Reviewed source at commit `0146170`, before the correction results were available. This review covers six current AlphaMissense Opus inline notebooks and STATE primary test 03 only. No isolated run or new STATE audit was inspected.

## AlphaMissense sampling unit and estimand

The declared fixed panel has 73 assays on 64 accessions; eight accessions have multiple assays (seven have two; P12931 has three). Existing per-assay measurements and selection rules should remain fixed. Resampling assays independently understates the shared-protein dependence. Resample accessions with replacement and retain every eligible assay in each selected protein block. Recompute the mean over the expanded assay rows, preserving the original assay-weighted estimand. An equal-weight average of protein means would be a different estimand.

For each curve point report finite assay count and distinct protein count. For paired high-minus-low and model-minus-comparator contrasts, retain the existing common set of assays with both endpoints for all three predictors, calculate paired assay contrasts first, then resample whole protein blocks. Do not independently resample models, levels, or assays. If a population estimate has fewer than two eligible proteins, report its descriptive point but no population interval. Save resampling seed, draw count and eligible cluster identifiers.

The existing endpoint contrasts condition on eligible paired assays, while marginal curves may have different eligible populations by level and predictor. Preserve that distinction rather than suggesting the displayed marginal endpoint subtraction must equal the paired headline estimate.

### Specific affected cells

- `am-opus-r1/test-01` and `test-03`: cell 18 assay bootstrap and Wilcoxon; dependent decision cell 20.
- `am-opus-r2/test-01` and `test-03`: cell 19 assay bootstrap and Wilcoxon; adjusted controls cell 21; dependent decision cell 23.
- `am-opus-r1/test-02` and `am-opus-r2/test-02`: cell 14 iid across-assay Spearman p-values; dependent decision cell 16.

### Paired tests

Remove the iid-assay Wilcoxon p-values. If a protein-block sign-flip test is retained, flip all assay contrasts for a protein together, use the original assay-weighted contrast statistic and state the joint sign-symmetry null assumption. This is not distribution-free evidence for an arbitrary zero-mean null. Exact enumeration can be used for small cluster counts; Monte Carlo tests need the plus-one correction. Do not label percentile-bootstrap tail counts as p-values.

### Continuous alignment-depth screen

Retain the original Spearman correlation across eligible assays. Draw proteins as blocks, repeat all their assay rows and recompute tied ranks/Spearman in every draw. Do not keep original ranks after duplication. Report distinct protein counts, finite bootstrap draw counts and a cluster interval; remove analytic iid Spearman p-values from the decision. An interval spanning zero is inconclusive, not evidence that depth has no association.

### R2 within-assay adjustments

Protein clustering must account for both repeated bins within an assay and multiple assays within a protein. Retain the current within-assay centering and point estimates. A finite-sample CR1 covariance should account for the absorbed assay fixed effects: full design rank equals the number of assay intercepts plus the rank of the centered slope matrix, not simply the four columns of the centered matrix with an intercept. A direct dummy-variable OLS fit with protein-cluster covariance provides an independent numerical check. Use t inference with G−1 degrees of freedom, report G and sample/design counts, and detect rank deficiency explicitly. The covariate-adjusted association is conditional and not a separate causal mechanism.

## STATE primary test 03

The current cell 16 bootstrap separately resamples low and high condition rows. Canonical genes repeat across contexts within each subset/representation and can appear in different levels across contexts. Draw from the union of canonical genes across both endpoints and preserve all context rows of each sampled gene. Per-draw weighted sums and counts must preserve the original row-weighted high-minus-low mean, rather than silently switching to an equal-weight gene mean. Report unique genes, endpoint row counts, valid draw counts and handling of empty endpoints.

Cell 18 already selects annotated extrema L1 and L2, but cell 20 currently decides from generic L0-to-L2 trends. Replace that decision with the actual annotated L1-to-L2 contrast and its corrected uncertainty. The unannotated L0 group is descriptive and cannot supply a third informative similarity level. Tied fixed cutpoints should not be repaired by outcome-driven splitting or jitter.

Retain the explicit evidence boundaries: reference membership reconstructed from released inventories and held-out lists; same benchmark and recurring genes across contexts; released STATE scores, not fresh inference; no full graded-curve protocol certification from two annotated levels.

## Provenance and reporting dependencies

All seven corrected notebook conclusions, tables, rendered images and HTML, execution receipts, `current_inline_analysis` metadata and preferred result descriptions must agree. Historical supporting code/results and their original receipts stay preserved under their existing historical scope. New execution must say exactly which cells ran and with which inputs; correcting downstream uncertainty does not establish that raw upstream feature extraction or model inference was rerun.

Changing uncertainty alone must not change cohort, axis construction, model scores, split membership or point estimates beyond numerical tolerance. Report any exception before integration. These are focused dependence corrections, not retrospective proof of independent discovery or external confirmation.
