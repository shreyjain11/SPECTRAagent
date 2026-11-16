# AlphaMissense primary uncertainty correction

Plan recorded before recalculation, November 15, 2026. Starting repository commit: `1d3b45b`.

The effective-depth endpoint in primary test 03 has one paired assay from one protein. Bootstrapping this assay repeatedly cannot estimate uncertainty across assays or proteins. Multiple other assays share proteins, so independent assay resampling also understates the clustering structure.

Keep every declared axis, bin boundary, eligible variant, score, endpoint direction and point-estimate weighting unchanged. Do not select a different endpoint or redefine levels in search of a positive result.

For the shared DMS workflow in primary tests 03–07:

1. Reuse hash-verified retained scored/per-assay tables from the current reconstruction. No new annotation acquisition or model inference.
2. Preserve variant-weighted curve means and the mean of within-assay endpoint differences. For uncertainty, sample proteins with replacement and carry all assays for the sampled protein together. Compute the original ratio estimand from the sampled cluster totals; do not silently change to an equal-protein estimand.
3. Use 5,000 bootstrap replicates, a fixed seed of 42, and 2.5/97.5 percentiles. Report both assay and independent protein counts.
4. For fewer than two proteins, leave uncertainty unavailable (NaN in calculation tables), retain the descriptive point estimate, and make the decision state insufficient independent replication. Also leave intervals unavailable when the empirical resampling distribution has no variation. Two proteins is a mechanical minimum, not evidence of adequate population coverage.
5. Display descriptive points without uncertainty bars where no interval can be estimated. Identify these in the plot and result text. Keep a separate occupancy contrast from being used to validate the depth endpoint.
6. Replace automatic acceptance from a one-assay interval with the explicit replication check. Supported intervals, where present, remain conditional cohort associations rather than full protocol or causal claims.

Primary tests 01–02 already resample by protein/gene and do not use this DMS helper. Inspect their cluster counts and decision guards; apply the same insufficient-unit safeguard only where it is relevant, without changing their large-cohort estimates gratuitously.

Record exact input paths, hashes, commands, executed cells/calculation stages, before/after tables, decisions and plots. Keep historical evidence in Git; do not replace evidence of a prior full execution with a claim of a fresh full execution. HTML and registry integration are separate.

## Retained-input route clarified before corrected uncertainty calculation

The previous Broad execution's per-assay CSV files were not recovered locally. Rebuild those statistics from three already-public repository payloads: the frozen panel/official-score subset, original DMS members, and recorded alignment arrays. Preserve all filters and scoring code. This reconstructs 270,572 variants in 72 assays and 63 proteins. Initial checks reproduce the printed AlphaMissense/BLOSUM statistics and exact composition-file hashes. The PSSM reference in test 06 has a small difference when using recorded rather than freshly reclustered profile counts (largest observed weighted curve difference about 0.0000073). Record that difference explicitly; do not claim byte-identical upstream recovery. No bins or endpoint were changed. Corrected uncertainty calculations will use this declared retained-input route, and execution receipts will identify the rerun stages rather than claiming full raw acquisition/alignment execution.
