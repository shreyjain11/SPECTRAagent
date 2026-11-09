# Axis-3 — AlphaMissense × positional alignability (SPECTRA): final deliverables

Curated final outputs for the AlphaMissense SPECTRA Axis-3 audit (MSA-column occupancy / hard-to-align
positions). **Scored panel = 72 assays / 63 proteins.** UBC9_HUMAN (P63279) passes the ≥99% identity
filter but fails exact full-length coordinate mapping at scoring (AM canonical 158 residues vs
ProteinGym target 159 residues), so it is excluded from the scored curve. All panel counts here are
consistent at 72/63.

**Result (settled):** all predictors decline on hard-to-align (low-occupancy) columns; the difficulty
is intrinsic (even position-blind BLOSUM62 declines and the DMS signal weakens), and AM is the most
accurate predictor at every bin with the smallest proportional decline — i.e. comparatively robust.

## Manuscript
- `alphamissense_results.tex` — results subsection (LaTeX). Panel counts at 72/63; confound numbers
  recomputed over the 72-assay panel. (Source: `stepB/alphamissense_results_v2.tex`.)

## Figure (panel count corrected to 72/63; plotted curve identical to prior v2 — no re-plot)
- `figure_axis3_SPC.pdf` / `.png` / `.svg` — 3-panel figure: (A) per-occupancy-bin accuracy for AM +
  site-independent PSSM + BLOSUM62 with real MSA-column cartoons; (B) deep-column interaction
  (Neff≥200); (C) DMS-signal (dynamic-range) control. (Source: `stepB/figure_axis3_SPC_v3.*`.)
- `figure_axis3_SPC_data.tsv` — reproducibility table behind the figure (per-bin |rho|, 95% CIs, n).

## Key result tables
- `axis3_baselines_binstats.tsv` — per-bin |rho| + 95% bootstrap CIs for AM / PSSM / BLOSUM62.
- `axis3_dms_signal_perbin.tsv` — within-assay DMS dynamic range (signal control) per bin.
- `axis3_SPC_perassay_bins.tsv` — per-(assay,bin) signed rho + n_variants (the scored 72-assay panel).
- `axis3_pathC_percolumn_FROZEN.tsv` — frozen per-column bins (occupancy / Neff / insert-state),
  fixed BEFORE scoring. Contains all 73 filter-passing assays incl. UBC9 (158 positions); the scored
  curve uses the 72 that map.

## Confound checks
- `confound_recheck_72.txt` — distinct proteins per bin, single-protein max fraction (q0 & insert),
  and internal-vs-terminal fractions for coarse-hard / q0 / insert / deep-and-gappy, reported as
  OLD (73, incl. UBC9) vs NEW (72, UBC9 excluded). This is the file the `.tex` confound numbers cite.
- `terminal_internal_check.txt` — original internal-vs-terminal confound over the 73-assay frozen file.
- `sign_concentration_checks.txt` — sign-stability + jackknife/concentration (computed from the scored
  per-assay TSV, already 72-based).
- `derived_stats_for_tex.txt` — easy→hard drops, AM−baseline |rho| gaps, intrinsic-difficulty
  counterfactual, DMS shrink % (the derived numbers used in the `.tex`).

## Reports
- `STEP_B_SCORING_RESULTS.md` — full scoring writeup (coarse / quintile / interaction / paired sign
  tests / sign-aware gaps / baselines).
- `STEP_B_PATHC_REPORT.md` — frozen-bins build + confound gate (why occupancy is the clean axis).

---
**Provenance note.** `terminal_internal_check.txt` and `STEP_B_PATHC_REPORT.md` report the original
73-assay frozen-file confounds; `confound_recheck_72.txt` supersedes their per-hard-bin protein counts
and internal fractions for the 72-assay scored panel (the `.tex` uses the 72 values). The 72/63
reconciliation was pure bookkeeping — **no Spearman / score was recomputed**; the only changes were
panel counts, the four confound numbers that shift by ≤1 protein / ≤0.6 pp, and the figure caption.
