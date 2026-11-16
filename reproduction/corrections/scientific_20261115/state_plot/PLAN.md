# STATE Codex r1 plot label correction

The first test-04 figure uses S-phase-score SD with ST-HVG error scores. Correct its x-axis and title; do not change its estimand, bootstrap method, seed or cohort.

Recompute the plotted table from the retained per-condition scores in reconstructed/state-codex-r1/computed/analysis/controls/per_condition_scores.csv: use hvg_best confirmation rows and join the S-phase axis by cell line. Use the existing 10,000 compound bootstrap and seed 20260714. Before accepting the new plot, require every point and interval to reproduce the old saved table at its displayed precision. This reruns one plot cell from retained records, not the raw acquisition/model-scoring pipeline. Save the input hash, reconstruction setup, code cell and recalculated table.
