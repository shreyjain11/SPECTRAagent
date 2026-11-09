# STATE SPECTRA Generalizability Audit

Run root: `/ewsc/yektefai/spectra_runs/state_generalizability_continued_20260603`

This run used official precomputed STATE result CSVs from the prior SPECTRA
session, not fresh STATE inference. The audit used 39,808 scored result rows
across Tahoe-100M, Replogle-Nadig, and Parse-PBMC, with HVG and SE
representations. Prospective metadata came from official split TOMLs, HGNC, and
Reactome.

## Primary Supported Axis

**Axis:** Replogle Reactome pathway train-support density.

For each held-out Replogle gene perturbation, the similarity score is the mean
`log(1 + number of same-context training genes sharing each Reactome pathway of
the target gene)`. Higher support means the target gene is closer to known
training biology in that target context.

Discovery contexts were `hepg2` and `k562`; confirmation contexts were `jurkat`
and `rpe1`. Split membership used only prospective gene/pathway metadata and
official train/test definitions, not target-model errors or reference-derived
outcomes.

### Few-Shot Confirmation

Held-out confirmation rows: 2,145 per representation.

| Representation | Low/no support mean overlap@N | High support mean overlap@N | High-low gap |
|---|---:|---:|---:|
| HVG | 0.2036 | 0.3313 | +0.1278 |
| SE | 0.1576 | 0.2670 | +0.1094 |

Excluding the no-annotation bucket, the confirmation high-low gaps were +0.1482
for HVG and +0.1280 for SE.

### Per-Context Control

High-low overlap@N gaps were positive in every tested context and
representation:

| Context | HVG gap | SE gap |
|---|---:|---:|
| hepg2 | +0.1949 | +0.1752 |
| k562 | +0.1275 | +0.0966 |
| jurkat | +0.1372 | +0.0734 |
| rpe1 | +0.1233 | +0.1198 |

### Cross-Protocol Zero-Shot Check

The same support idea was applied to Replogle zero-shot by using training genes
from the other cell contexts and normalizing support by train-set size. This
used 5,759 rows per representation.

| Representation | Low/no support mean overlap@N | High support mean overlap@N | High-low gap |
|---|---:|---:|---:|
| HVG | 0.1095 | 0.1771 | +0.0676 |
| SE | 0.0563 | 0.0999 | +0.0437 |

### Confound Checks

The trend remained after excluding the no-annotation bucket and within
pathway-count matched bins. A simple OLS control over context, representation,
subset, Reactome pathway count, and label-derived DE-count severity kept a
positive support coefficient for overlap@N (`+0.0284`, t=14.36). DE-count
severity was much larger (`+0.1629`), so perturbation strength is an important
outcome confound/mediator, but it did not fully explain the support axis.

## Negative / Non-Terminal Axes

- Prior Tahoe target-context chemical Tanimoto support was split-valid but
  negative/weak: no meaningful degradation with lower chemical support.
- Parse-PBMC ligand-family training support reversed direction: higher
  same-family support did not improve overlap@N in discovery or confirmation.

## Current Interpretation

STATE appears to generalize worse for Replogle gene perturbations whose Reactome
pathways are sparsely represented among training perturbations. This boundary
holds across held-out few-shot contexts and also weakly but consistently in the
harder Replogle zero-shot protocol.

This is a current-pool confirmed SPECTRA axis, not yet a raw-data rerun. The
main remaining reviewer-facing gap is a fixed baseline or raw-label rerun, which
requires raw single-cell matrices/predictions rather than only official scored
CSV outputs.

## Cross-Ontology Extension

To test whether this was Reactome-specific, the same SPECTRA protocol was
repeated with independent prospective gene-set systems: HGNC gene groups, GO
Biological Process, GO Molecular Function, GO Cellular Component, WikiPathways,
and KEGG. For each collection, support levels were frozen from `hepg2+k562`
few-shot discovery contexts, then evaluated on `jurkat+rpe1` few-shot
confirmation and Replogle zero-shot cross-protocol confirmation.

| Collection | Few-shot HVG gap | Few-shot SE gap | Zero-shot HVG gap | Zero-shot SE gap |
|---|---:|---:|---:|---:|
| Reactome | +0.1144 | +0.0853 | +0.0676 | +0.0437 |
| HGNC gene group | +0.1144 | +0.0935 | +0.0678 | +0.0471 |
| GO Biological Process | +0.1614 | +0.1345 | +0.0873 | +0.0568 |
| GO Molecular Function | +0.0143 | +0.0545 | +0.0348 | +0.0484 |
| GO Cellular Component | +0.1215 | +0.0901 | +0.0812 | +0.0548 |
| WikiPathways | +0.1039 | +0.1266 | +0.0346 | +0.0344 |
| KEGG | +0.1415 | +0.1278 | +0.0664 | +0.0467 |

This supports the broader claim: the degradation is not Reactome-specific. It
is a pathway/module train-coverage effect. The strongest independent support
came from GO Biological Process, KEGG, WikiPathways, Reactome, HGNC groups, and
GO Cellular Component. GO Molecular Function had positive high-low gaps, but its
controlled few-shot coefficient was weak compared with the other systems.

High-support bins were dominated by recurrent biological modules such as
translation, ribosome, RNA metabolism, mRNA splicing, rRNA processing,
mitochondrial translation, cytoplasmic ribosomal proteins, and spliceosome
pathways.

## Key Artifacts

- `artifacts/replogle_refined_axis_screen.csv`
- `artifacts/spc_replogle_best_refined_axis.csv`
- `artifacts/spc_replogle_best_refined_axis_trends.csv`
- `artifacts/spc_replogle_best_refined_axis_context_trends.csv`
- `artifacts/controls_replogle_best_axis_high_low_gaps.csv`
- `artifacts/controls_replogle_best_axis_pathway_count_matched.csv`
- `artifacts/controls_replogle_best_axis_regression.json`
- `artifacts/spc_replogle_zeroshot_reactome_support_confirmation.csv`
- `artifacts/spc_replogle_zeroshot_reactome_support_confirmation_trends.csv`
- `artifacts/multi_pathway_support_screen.csv`
- `artifacts/multi_pathway_support_summary.json`
- `artifacts/multi_pathway_top_features_by_support_level.json`
- `spectra_ready_dataset/state_replogle_reactome_pathway_log_train_support_v2_examples.csv`
- `spectra_ready_dataset/replogle_zeroshot_reactome_support_confirmation_examples.csv`
