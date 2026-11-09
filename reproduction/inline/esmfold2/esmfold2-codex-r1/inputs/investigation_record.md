# Final SPECTRA report: released ESMFold2

**Closure verdict: CONFIRMED_GENERALIZABILITY_FAILURE.** A real prospective generalizability failure of released ESMFold2 is certified along the frozen axis.

No artifact was submitted to the SPECTRA pending queue. This report closes only the frozen ESMFold2 audit in this workspace.

## Frozen claim and separation

The prospective input-side axis is the maximum Jaccard similarity between a post-cutoff chain’s set of distinct Pfam-A accessions and the repertoire of any PDB protein chain released on or before 2021-09-30. L0 is exact repertoire overlap (1.0), L1 is 0.67–<1.0, L2 is 0.34–<0.67, and L3 is <0.34. Lower similarity was hypothesized to reduce target-normalized TM-score.

The axis, direction, levels, model settings, primary metric, reference, controls, power target, and success gates were frozen before ESMFold2 structural scoring. The amendments were outcome-blind feasibility/QC amendments: SIFTS supplied repertoire rather than residue-range adjacency; combined clustering corrected representative availability; and uniform reference-only QC moved primary coordinate coverage from 0.80 to 0.70 while mandating a full ≥0.80 sensitivity. Metadata and the published crop curriculum formed discovery evidence; all 2,530 frozen examples were confirmation evidence scored once after the final freeze.

Frozen specifications: `config/frozen_axis_v1.json`, `config/frozen_axis_amendment_v2.json`, `config/frozen_panel_amendment_v3.json`, `config/frozen_panel_qc_amendment_v4.json`, and `config/frozen_reference_qc_amendment_v5.json`.

## Released model and task

The audited model is the full released `biohub/ESMFold2` checkpoint at `1ebf0e3481a5184eb6171d40615c79e384b48796`, with full `biohub/ESMC-6B` at `45b0fa5d7fb06faefbd5e3b89bdcef35d564e79a`. The Fast variant was excluded. Biohub ESM code commit is `ba4d7124864eed323a93bf3cfefcd958f573b75a` and Biohub Transformers commit is `3a8956fb4d4ea16b0ec8e71deef2c2909b6a5cbf`. Inference used one sequence/chain, no MSA, 3 loops, 68 diffusion steps, one sample, seed 0, and the official full-model loader (folding parameters fp32; ESMC parameters bf16).

The pinned released source used xformers where applicable and its own explicit pure-PyTorch fallbacks for optional Transformer Engine fused LayerNorm/MLP and flash-attention rotary kernels. Those optional fusions change implementation-level rounding, not the model/checkpoint or architecture; the full 6B language model and folding trunk were present and the path was fixed for every target. `provenance/implementation_notes.json` preserves the exact resolution and source warning.

Acceleration was verified on `NVIDIA A100-SXM4-40GB, GPU-1f93a14f-2476-cac5-716b-79c48a995d7c, 550.90.07, 40960 MiB, 8.0`. The boot disk was expanded from 350 GB to 450 GB solely to retain the exact full checkpoints and complete per-target artifacts; no scientific specification changed.

The panel consists of 2,530 unique 40%-identity/80%-coverage MMseqs2 clusters: 2,000 primary-axis chains and 530 published short/single-domain controls. Experimental targets are X-ray or cryo-EM PDB chains released 2021-10-01 through 2026-06-30, length 40–1,024, resolution ≤3.5 Å, with ≥70% experimental Cα coverage. The primary outcome is US-align TM-score normalized by experimental target length.

## Power and measured ordering

The frozen one-sided design used minimum effect 0.04, assumed SD 0.18, α=0.025, power 0.80, and required at least 318 examples in each extreme. Observed L0=1,517 and L3=322, so the declared count target passed.

| Level | n | Median similarity | Bootstrap 95% CI |
| --- | --- | --- | --- |
| L0 | 1517 | 1.000 | [1.000, 1.000] |
| L1 | 30 | 0.750 | [0.750, 0.750] |
| L2 | 131 | 0.667 | [0.667, 0.667] |
| L3 | 322 | 0.250 | [0.250, 0.310] |

Strict median ordering L0>L1>L2>L3: **True**.

## Spectral performance curve and uncertainty

All intervals below are 10,000-replicate frozen-seed nonparametric bootstrap 95% intervals.

| Metric | Level | n | Mean | 95% CI |
| --- | --- | --- | --- | --- |
| Target-normalized TM-score | L0 | 1517 | 0.857 | [0.849, 0.864] |
| Target-normalized TM-score | L1 | 30 | 0.796 | [0.729, 0.857] |
| Target-normalized TM-score | L2 | 131 | 0.777 | [0.746, 0.807] |
| Target-normalized TM-score | L3 | 322 | 0.761 | [0.741, 0.781] |
| Cα lDDT | L0 | 1517 | 0.888 | [0.884, 0.891] |
| Cα lDDT | L1 | 30 | 0.870 | [0.853, 0.886] |
| Cα lDDT | L2 | 131 | 0.854 | [0.839, 0.867] |
| Cα lDDT | L3 | 322 | 0.853 | [0.844, 0.861] |
| Aligned Cα RMSD (Å) | L0 | 1517 | 2.340 | [2.271, 2.409] |
| Aligned Cα RMSD (Å) | L1 | 30 | 2.866 | [2.370, 3.393] |
| Aligned Cα RMSD (Å) | L2 | 131 | 3.059 | [2.834, 3.290] |
| Aligned Cα RMSD (Å) | L3 | 322 | 2.804 | [2.664, 2.950] |
| Mean predicted pLDDT (0–1) | L0 | 1517 | 0.875 | [0.871, 0.879] |
| Mean predicted pLDDT (0–1) | L1 | 30 | 0.865 | [0.841, 0.887] |
| Mean predicted pLDDT (0–1) | L2 | 131 | 0.859 | [0.848, 0.870] |
| Mean predicted pLDDT (0–1) | L3 | 322 | 0.846 | [0.837, 0.854] |
| Predicted pTM | L0 | 1517 | 0.812 | [0.805, 0.819] |
| Predicted pTM | L1 | 30 | 0.758 | [0.692, 0.818] |
| Predicted pTM | L2 | 131 | 0.748 | [0.723, 0.774] |
| Predicted pTM | L3 | 322 | 0.729 | [0.711, 0.746] |

Primary L0−L3 TM-score contrast: **0.096**, two-sided 95% CI [0.075, 0.116], one-sided 97.5% lower bound 0.075, bootstrap P(contrast>0)=1.0000. The isotonic trend gate passed: **True**.

Machine-readable SPC: `outputs/analysis/spectral_performance_curve.csv`; plot: `plots/spectral_performance_curve.png`; per-example merged table: `outputs/analysis/analysis_table.csv`.

## Same-example model-independent reference

The fixed reference searches pre-cutoff PDB chains with MMseqs2, selects the deterministic best hit, globally aligns query/template, and transfers matched template Cα coordinates. It is a genuine model-independent 3D predictor on the same chains and metric; it characterizes shared versus model-specific degradation but cannot by itself remove intrinsic structural difficulty.

Intention-to-predict included all 1839 L0/L3 primary examples, assigning zero to reference failures: ESMFold2 Δ=0.096, reference Δ=0.473, and Δ_ESMFold2−Δ_reference=-0.378 with 95% CI [-0.415, -0.341]. The explicit gate answer to “Does ESMFold2 degrade at least as much as the model-independent reference?” is **False**. Because the fixed reference degrades substantially more, this is characterized as **shared axis degradation, with less degradation for ESMFold2 than for the reference**, rather than model-specific excess degradation.

The complete-reference-case sensitivity used 1744 extreme examples: ESMFold2 Δ=0.097, reference Δ=0.348, difference=-0.252, 95% CI [-0.285, -0.217], gate=False. Reference status counts were {'scored': 2328, 'no_hit': 196, 'fewer_than_3_mapped_ca': 6}. Reference degradation is reported as characterization, not a veto.

## Homology, length, and frozen controls

| Level | n | Mean length | Mean best-hit identity | Mean best-hit qcov | Mean coordinate coverage | Mean Pfam count |
| --- | --- | --- | --- | --- | --- | --- |
| L0 | 1517 | 459.4 | 0.791 | 0.933 | 0.919 | 2.37 |
| L1 | 30 | 683.0 | 0.529 | 0.780 | 0.899 | 3.97 |
| L2 | 131 | 537.0 | 0.569 | 0.686 | 0.911 | 2.79 |
| L3 | 322 | 457.8 | 0.393 | 0.437 | 0.908 | 2.18 |

The fully adjusted continuous-similarity coefficient was 0.053 (HC3 SE 0.016, one-sided p=0.00044, n=2000). The adjusted L0−L3 coefficient was 0.045 (HC3 SE 0.013, one-sided p=0.00034).

The model jointly adjusted a 4-df natural cubic spline for length, nearest pre-cutoff identity/query coverage/no-hit, release date, experimental method, resolution, coordinate coverage, Pfam count/coverage, taxonomy, TANTAN low complexity, metapredict disorder, NCOILS coiled coil, and multimeric assembly. Homology- and length-stratified tables are `outputs/analysis/homology_stratified.csv` and `outputs/analysis/length_stratified.csv`.

| Single control | Adjusted L0−L3 | One-sided p | Fraction removed | Invalidates |
| --- | --- | --- | --- | --- |
| length | 0.094 | 0.0000 | 0.014 | False |
| homology | 0.042 | 0.0024 | 0.563 | False |
| release_date | 0.096 | 0.0000 | 0.001 | False |
| method | 0.087 | 0.0000 | 0.091 | False |
| resolution | 0.071 | 0.0000 | 0.259 | False |
| coordinate_coverage | 0.092 | 0.0000 | 0.042 | False |
| pfam_count_coverage | 0.101 | 0.0000 | -0.052 | False |
| taxonomy | 0.092 | 0.0000 | 0.042 | False |
| low_complexity | 0.096 | 0.0000 | 0.001 | False |
| disorder | 0.093 | 0.0000 | 0.025 | False |
| coiled_coil | 0.092 | 0.0000 | 0.038 | False |
| oligomeric_state | 0.098 | 0.0000 | -0.024 | False |

No single nuisance/measurement control removed >80% while eliminating the signal: **True**. Frozen controls covered all 2,530 rows; 196 had no pre-cutoff hit, 114 had unknown superkingdom, and 2010 were annotated multimeric.

## Mandatory and secondary sensitivities

The mandatory ≥80% experimental-Cα-coverage repeat used n=1750 with level counts {'L0': 1342, 'L1': 24, 'L2': 112, 'L3': 272}. It repeated every metric SPC, the same-example reference gate, the full HC3-adjusted models, and all single-confound checks. Its ESMFold2 L0−L3 TM contrast was 0.094, 95% CI [0.072, 0.115]; adjusted continuous-similarity coefficient 0.053, one-sided p=0.00097; no invalidating single control=True.

The monomeric-assembly sensitivity used n=407 and gave ESMFold2 Δ=0.051, 95% CI [0.014, 0.088], reference gate=False. The reference-complete sensitivity used n=1899 primary examples and gave ESMFold2 Δ=0.097, 95% CI [0.073, 0.121].

## Candidate dispositions

Raw length and homology support were rejected as novel primary axes because they are published controls; both were retained quantitatively. Disorder and coiled-coil burden were measured prospectively as confounds. Membrane topology was not tested independently, and no membrane-axis negative is claimed. Full dispositions, including the distinction between ‘not required’ and a genuine negative, are in `outputs/analysis/candidate_axis_disposition.csv`.

| ID | Axis | Final disposition | Reason |
| --- | --- | --- | --- |
| A01 | Pfam domain-repertoire proximity | CONFIRMED_GENERALIZABILITY_FAILURE | Frozen primary axis passed every confirmatory gate. |
| A02 | Raw sequence length | PUBLISHED_CONTROL_NOT_NOVEL_AXIS | Length was retained in the spline adjustment and stratified summaries. |
| A03 | Sequence homology support | PUBLISHED_CONTROL_AND_REFERENCE_NOT_NOVEL_AXIS | Homology identity/coverage were adjusted and coordinate transfer supplied the fixed reference. |
| A04 | Intrinsic disorder burden | MEASURED_CONFOUND_NOT_INVALIDATING_PRIMARY | Measured prospectively as a sequence-only control; it did not invalidate the confirmed primary axis. No axis-level negative is claimed. |
| A05 | Coiled-coil/repeat burden | MEASURED_CONFOUND_NOT_INVALIDATING_PRIMARY | Measured prospectively as a sequence-only control; it did not invalidate the confirmed primary axis. No axis-level negative is claimed. |
| A06 | Membrane topology | NOT_REQUIRED_AFTER_PRIMARY_CLOSURE | Not tested as an independent axis; no membrane-axis result is claimed. |

## Exact-match novelty

The frozen exact-match definition required released biohub/ESMFold2 structural accuracy quantified along the same nearest-pre-cutoff PDB Pfam-repertoire Jaccard axis (or an operationally identical axis). Searches through 2026-07-17 covered OpenAlex (25 unique records), Europe PMC (8), Crossref, GitHub issues (111), the released paper, and the model repository. Exact match found: **False**. This establishes exact-match novelty only, not broad conceptual novelty; indexing lag and unindexed/private work remain limitations.

## Provenance, integrity, and remaining gaps

Released ESMFold2 inference produced 2530 scored targets with status {'scored': 2530}. Atomic gzip-CIF predictions, the append-and-fsync JSONL ledger, per-target scores, checkpoint hashes, source commits, package lock, runtime hardware, raw download manifests, and frozen-file hashes all remain in this workspace. The final integrity result is `provenance/integrity_validation.json`; the complete file snapshot is `provenance/workspace_files.json`.

Remaining limitations are scientific rather than missing closure artifacts: 114 taxonomy values are explicit unknowns; the homology reference has no prediction for 196 chains and fewer than three mapped residues for 6 (handled by intention-to-predict plus complete-case analysis); the exact-match literature search may miss newly released or unindexed work; and single-chain prediction cannot represent binding partners or biological-assembly context. These do not change the frozen gate calls.

## Explicit gate calls and closure

| Gate | Pass |
| --- | --- |
| axis ordering | True |
| real degradation | True |
| adjusted attribution | True |
| no invalidating single confound | True |
| trend | True |
| reference comparison completed | True |
| all primary gates pass | True |

Final verdict: **CONFIRMED_GENERALIZABILITY_FAILURE**. The same-example reference answer is **False**, characterizing the result as shared axis degradation with ESMFold2 less affected than the reference. Under the corrected closure rule this does not veto the real prospective ESMFold2 degradation. No frozen specification was changed after outcomes, and nothing was submitted to the SPECTRA pending queue.
