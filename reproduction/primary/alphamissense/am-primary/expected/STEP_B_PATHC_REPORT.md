# Step B Path-C — Frozen bins + confound report (UniRef→ProteinGym v1.3 MSAs, theta=0.2)

**Date:** 2026-06-10. SCREEN/PREP ONLY — no AM scoring. Residue unit = distinct (accession, target_pos).
Per-column DEPTH = theta=0.2 weighted Neff (self-computed via 80%-id clustering; validated vs MSA_N_eff).
Per-column OCCUPANCY = raw non-gap fraction. 17,536 assay-positions → 13,115 aligned distinct
protein-positions + 1,774 insert-state (ProteinGym sub-threshold = unalignable hard end).

## DEPTH axis — original absolute edges FAIL; quantile edges PASS (but protein-limited)
Realized per-column Neff: min~0, p10=168, p25=495, **median=4799**, p75=11836, max=522197.
The specified absolute edges (<2/2-10/10-50/50-200/≥200) are far below this scale → **89% in ≥200**,
and the hard bins are degenerate/confounded:
- `<2`: 6 residues, **1 protein** (HXK4) → confounded
- `2-10`: 7 residues, 2 proteins (CAR11 71%) → confounded
- `10-50`: 166 residues, 8 proteins (CAR11 82%) → confounded

With **quantile** edges the sparse end is salvageable: q0 (Neff≤406) = 2624 residues, **21 proteins,
top 18%** (no majority). So depth is viable ONLY with data-driven edges, not the absolute ones.
Caveat: absolute per-column depth ≈ (weighted occupancy) × (protein global Neff), so the depth-sparse
end is dominated by the few genuinely orphan proteins + gappy columns — inherently ~20 proteins, and
correlated with occupancy by construction.

## OCCUPANCY axis — populated, UNCONFOUNDED hard end (the clean axis)
Realized occupancy: min=0, p5=0.736, p10=0.849, p25=0.960, median=0.994, max=1.0. Quintile edges
[0.945, 0.987, 0.998, 0.999].
- q0 (gappiest, occ≤0.945): 2625 residues, **56 proteins, top 9%** → UNCONFOUNDED
- insert-state (occ<threshold, hardest): 1774 residues, **49 proteins, top 13%** → UNCONFOUNDED

Occupancy varies *within* every protein, so its hard end pools from ~all proteins — exactly the
per-residue escape from the Axis-1 trap.

## INTERACTION — deep AND low-occupancy (the decisive "hard-to-align ≠ shallow" cell)
Among DEEP columns (Neff≥200, n=11,647; occ down to 0.114):
- DEEP & occ<0.5: 124 residues, **23 proteins**, top 19%
- DEEP & occ<0.7: 291 residues, **28 proteins**, top 14%
- DEEP & occ<0.9: 1286 residues, 48 proteins, top 9%

The deep-but-gappy cell is **populated and unconfounded** (23–28 proteins, no majority) — the sharpest
claim ("AM degrades on intrinsically hard-to-align positions even where homologs are abundant") has
empirical support on this panel.

## Gate verdict (per axis: populated + unconfounded hard end?)
- **OCCUPANCY: PASS** (clean, 56/49 proteins, no majority).
- **DEPTH: FAIL on the specified absolute edges** (1–2 proteins); PASS only with quantile edges
  (~21 proteins) — needs edge re-spec, and is inherently protein-limited + correlated with occupancy.
- **INTERACTION: PASS** (23–28 proteins).

## Recommendation (not a silent pick)
Occupancy is the primary, cleanest "hard-to-align" axis; the deep-but-gappy interaction is the
decisive test and it holds. Depth is viable only as a secondary axis with quantile edges, flagged as
protein-limited and occupancy-correlated. Decision needed before scoring: (a) adopt occupancy quintile
edges; (b) for depth, replace the absolute edges with quantile edges or drop depth to secondary.

## Files (new, no overwrites)
- `stepB/axis3_pathC_percolumn_FROZEN.tsv` — per assay-position depth/occupancy/lowcov/depth_bin
- `stepB/build_axes.log`, `stepB/STEP_B_PATHC_REPORT.md`
