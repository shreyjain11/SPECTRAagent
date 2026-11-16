# STATE scientific correction plan

Frozen before calculating corrected results on 2026-11-15. Baseline: commit `1d3b45b`. Scope: STATE Kimi r1 tests 01–04 and STATE Opus r2 test 05. No new model inference or fitting of STATE.

## Kimi pooled statistics

Preserve the per-context cohorts, metrics and primary point estimates. Recalculate the pooled binary seen-minus-unseen difference (equal context weights) and the pooled embedding-norm Spearman correlation (Fisher transform with fixed original context weights n_unseen − 3). Replace the invalid or independence-based pooled Z/p calculations with 95% percentile intervals from 10,000 joint gene-cluster bootstrap draws, seed 20261115. Sample the union of gene identities with replacement; retain every observed row/context of each sampled gene, including its multiplicity. Recompute rank ties within each draw rather than weighting fixed original ranks. This propagates dependence for genes repeated across contexts; it is conditional on the three observed contexts and does not infer independent site/experiment replication. Do not manufacture a pooled p value. Save draws and exact input hashes. Preserve individual-context calculations, explicitly distinguishing them from pooled uncertainty.

## Opus context adjustment

Replace arbitrary numeric context codes with one-hot context indicators (one reference category omitted) when residualizing ranked overlap and ranked neighborhood density. Rank continuous effect-size and coverage controls; do not rank the category indicators. Return the Pearson correlation between residuals. Use a 10,000-draw gene-cluster percentile bootstrap with seed 20261115 for the two displayed partial-rank specifications, recomputing ranks/design in each draw. Drop naive independent-row p values for these corrected partial fits. Keep other exploratory Spearman summaries labelled as descriptive row-level calculations.

## Opus sensitivity split and labels

Sort unique genes by SHA-256 of the UTF-8 string `STATE-OPUS-R2-sensitivity-v1|` followed by the gene identifier (gene identifier breaks any hash ties), then assign alternating ranks to halves 0/1. Save the complete gene/hash/half membership table. This balances gene counts to within one. It is a reproducible sensitivity split created during correction, not a retrospective claim of a prospectively frozen or independent confirmation split. Correct misleading module-removal and pure-training-coverage print labels to describe density trimming and above-median observed DE count.

## Evidence and acceptance checks

Verify retained inputs against public/source manifests or baseline calculation values, document any reconstruction, and preserve baseline original files in Git. Execute every changed code cell and downstream cell using its changed results. Save before/after output summaries, affected cell indexes, source/output hashes, execution commands, package versions and input hashes. Confirm repeated implementations agree across all four Kimi entries; verify split balance/determinism and compare bootstrap implementations with direct repeated-row resampling on fixed draws. Changes to HTML/registry and publication are handled by the parent task. This plan does not select methods after seeing corrected estimates.
