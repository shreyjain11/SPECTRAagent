# SPECTRA generalizability audit of STATE — final closure report

Closed: 2026-07-17 22:51:46 UTC  
Controller: single persistent controller in this workspace  
Queue action: none; nothing was submitted to the SPECTRA pending queue

## Executive verdict

**Closure verdict: `CLOSED_NEGATIVE_NO_CERTIFIED_GENERALIZABILITY_FAILURE`.**

The audit found several strong context associations but no candidate met every frozen closure condition:

1. The original prospective basal-transcriptomic-distance axis failed in the opposite direction: farther held-out contexts had *lower*, not higher, adjusted STATE error.
2. The reserved untouched ST-SE confirmation of baseline S-phase-score heterogeneity produced a strong positive compound-blocked regression, but its five context means were non-monotonic (Spearman rho 0.30 versus the frozen minimum 0.70). It is therefore an honest axis-level negative under its frozen gate.
3. The pre-ledgered training-lineage-scarcity follow-up passed its overall slope and shape checks on `eval_last`, but failed the frozen stability condition, reversed when HepG2/C3A was excluded, disagreed in direction with the ST-HVG discovery partition, and is not independently prospective because its exact operationalization followed access to the related `eval_best` checkpoint.

No result was promoted by changing a specification after seeing its outcome. No additional clean, same-design, untouched STATE/Tahoe confirmation surface remains in the public release.

## 1. Original frozen axis and prospective ordering

The original contract, [frozen_axis.yaml](specs/frozen_axis.yaml), was frozen before any STATE outcome access. The input-side axis was basal transcriptomic distance from the STATE training panel:

- Primary atlas: Sanger Cell Model Passports RNA-seq, log2(TPM + 1).
- Genes: 2,000 highest-variance protein-coding symbols selected in the 44 mapped training contexts only.
- Standardization: training-context gene mean and sample SD.
- Distance: RMS standardized Euclidean distance, aggregated as the median of the five nearest training-context distances.
- Frozen order, near to far: HOP62 0.953059; PANC-1 1.062149; Hs 766T 1.131635; C32 1.254312; HepG2/C3A 1.404170.

The independent CCLE/DepMap 23Q4 atlas used 1,832 intersecting genes and 43 training contexts. Its order was identical: HOP62 0.995532; PANC-1 1.087685; Hs 766T 1.196330; C32 1.264095; parental HepG2 proxy 1.363152. Rank Spearman rho was 1.0. Restricting to the four exact, non-proxy contexts also gave rho 1.0.

## 2. Discovery/confirmation separation and power

Normalized parent compounds were assigned by SHA-256: the first 16 hexadecimal digits modulo 10. Buckets 0–2 were discovery and buckets 3–9 were untouched confirmation. All doses and contexts for a parent compound stayed in one partition.

The prospective Monte Carlo plan specified a one-SD effect of 0.15 residual-SD RMSE, one-sided alpha 0.05, two or more doses, and at least 150 confirmation compounds. Simulated power at 150 clusters was 0.8639. The complete eligible panel contained 379 compounds and 1,136 drug-dose targets; confirmation contained 268 compounds, 804 targets, 4,020 context-condition rows, and five contexts. The count and power gates were exceeded without expanding or selecting conditions from outcomes.

## 3. Original distance-axis result

On ST-HVG `eval_best`, the untouched confirmation result was:

| Analysis | Slope per axis SD | 95% compound-bootstrap CI | One-sided p |
|---|---:|---:|---:|
| STATE raw | -0.03221 | [-0.04254, -0.02210] | approximately 1 |
| STATE adjusted | -0.15004 | [-0.15945, -0.13968] | 1 |
| Identity reference raw | +0.16321 | [0.15443, 0.17219] | 2.1e-287 |

Adjustment included same-example identity-reference RMSE, log1p observed DE-gene count, log1p observed cell count, and within-drug-dose centering, with parent-compound cluster inference. Effect/cell-count-quintile matching remained negative (-0.12478). All three dose-stratified estimates and all five leave-one-context-out estimates were negative.

The paired compound-bootstrap STATE-minus-reference raw slope CI was [-0.20141, -0.18914], so STATE's distance slope was smaller than the reference's. This does not reject a genuine STATE degradation under the corrected reference rule; here, however, STATE itself did not degrade along the frozen axis.

Independent-atlas confirmation was also negative: adjusted CCLE-distance slope -0.12962, 95% CI [-0.13977, -0.11902]. The four-exact-context sensitivity was -0.07886, 95% CI [-0.08809, -0.06963]. The original distance candidate is therefore an axis-level negative, not a failure finding.

## 4. Frozen S-phase-heterogeneity candidate and untouched ST-SE confirmation

After the original candidate failed, discovery-only ST-HVG evidence identified baseline untreated-cell S-phase-score heterogeneity. The reserved contract is [frozen_s_phase_axis.yaml](specs/frozen_s_phase_axis.yaml). It used the sample SD of released per-cell `S_score` among Tahoe `DMSO_TF` controls. All 319,511 baseline cells reproduced the frozen values exactly:

| Frozen level | Context | S-score SD | Baseline cells | ST-SE confirmation mean RMSE |
|---:|---|---:|---:|---:|
| 1 | C32 | 0.120724 | 51,984 | 2.9997 |
| 2 | HOP62 | 0.144538 | 78,130 | 2.6530 |
| 3 | HepG2/C3A | 0.202683 | 31,538 | 3.4001 |
| 4 | PANC-1 | 0.244544 | 97,098 | 2.7259 |
| 5 | Hs 766T | 0.328889 | 60,761 | 3.1656 |

Odd- versus even-numbered plates independently reproduced the same ordering (rank rho 1.0). Restricting baseline measurement to cells with `pass_filter == full` also preserved the exact order (rho 1.0), arguing against a failed-QC-cell artifact.

The untouched ST-SE `eval_best` confirmation used the same 268 compound clusters, 804 drug-dose targets, 4,020 rows, full released feature panel, and 10,000 compound bootstraps:

| Analysis | Slope per S-axis SD | 95% compound-bootstrap CI | One-sided p |
|---|---:|---:|---:|
| ST-SE raw | +0.08056 | [0.07013, 0.09109] | 5.1e-50 |
| ST-SE adjusted | +0.09515 | [0.08586, 0.10475] | 2.4e-87 |
| Identity reference raw | -0.03870 | [-0.05153, -0.02608] | approximately 1 |

The paired ST-SE-minus-reference raw slope was +0.11927, 95% CI [0.11232, 0.12631]: the STATE degradation was larger than the fixed reference's.

### Effect magnitude, cell count, and other controls

- Continuous adjustment for identity RMSE, DE count, and cell count: +0.09515.
- Effect-magnitude and cell-count quintile matching: +0.10494.
- Dose-specific adjusted slopes: +0.08886 at 0.05 uM, +0.09061 at 0.5 uM, and +0.10787 at 5 uM.
- Leave-one-context-out adjusted slopes: all positive, from +0.06716 to +0.13123.
- Confirmation observed-cell counts ranged from 1 to 57,193; median 1,856.5. Conditions with zero `full` cells used their observed all-cell count according to the frozen rule.
- Chemical modality, 24-hour exposure, ST-SE checkpoint family, and X_state representation were fixed.

Despite these stable regressions, the context-mean spectral curve had rho 0.30, below the frozen 0.70 threshold. C32 and HepG2/C3A were high-error contexts at relatively low/intermediate S heterogeneity, and PANC-1 was lower-error at level 4. More sampling of the same 804 targets would tighten uncertainty but would not repair the prespecified ordering. The candidate is therefore ledgered as `axis_negative_strong_regression_but_shape_failed`.

## 5. Training-lineage-scarcity follow-up

The candidate ledger predated ST-SE access and named tissue/lineage distance as a secondary candidate. After the two frozen failures, it was operationalized as `-log(1 + number of mapped training contexts sharing the held-out DepMap Oncotree lineage)` and recorded in [frozen_lineage_scarcity_axis.yaml](specs/frozen_lineage_scarcity_axis.yaml) before any ST-SE `eval_last` file was opened.

The four levels were Lung/HOP62 (14 training contexts), Pancreas/PANC-1 and Hs 766T (4), Skin/C32 (3), and Liver/HepG2/C3A (1). On the untouched `eval_last` files, adjusted slope was +0.03223, 95% CI [0.02232, 0.04195], and context rho was 0.82078. The identity reference shared most of the raw curve; STATE-minus-reference raw slope was +0.01266, 95% CI [0.00291, 0.02258].

This did not close:

- The 5 uM adjusted slope was +0.01027 with one-sided p 0.0827.
- Excluding HepG2/C3A reversed the adjusted slope to -0.01196.
- The ST-HVG discovery-partition adjusted direction was negative (-0.07233).
- Exact operationalization occurred after access to the related `eval_best` checkpoint, so `eval_last` is supportive but not an independent prospective confirmation.

It is ledgered as an axis-level negative follow-up and is not closure eligible.

## 6. Same-example fixed references

Every primary comparison used an identity/no-effect predictor: zero log2 fold-change for each feature. It consumed no held-out outcome to make a prediction. STATE and reference RMSE were computed on the same target, context, feature rows, and full feature representation. Reference-slope differences used paired compound-bootstrap resamples, not independent bootstrap draws.

Reference gate calls were:

- Original distance/ST-HVG: STATE degradation smaller; STATE itself improved with distance.
- S-phase/ST-SE `eval_best`: STATE degradation larger; nevertheless the frozen shape gate failed.
- Lineage/ST-SE `eval_last`: STATE degradation slightly larger; stability and prospectivity gates failed.

## 7. Rejected candidates and confound ledger

- Basal transcriptomic distance: rejected by negative raw, adjusted, matched, dose-stratified, leave-one-context-out, and independent-atlas slopes.
- Baseline S-phase-score heterogeneity: rejected for non-monotonic five-context shape despite strong adjusted and controlled slopes.
- Training-lineage scarcity: rejected for dose/leave-one-context instability, cross-representation direction disagreement, and prospectivity qualification.
- True perturbation magnitude, DE count, and cell count: used as controls and re-attribution checks; none alone justified relabeling a certified axis.
- Dose: blocked/stratified; fixed candidate conclusions did not arise from a single selected dose.
- Modality and exposure: fixed to small-molecule perturbations at 24 hours.
- Checkpoint and representation: explicitly recorded for each analysis; no outcome-dependent switch was used to certify a finding.

## 8. Exact-match novelty

The dated search and source table are in [novelty_search.md](results/novelty_search.md). The official STATE repository/paper, Tahoe-100M paper, recent Tahoe benchmark papers, and targeted exact queries revealed no prior report matching STATE, the same Tahoe zero-shot contexts, the same S-score-heterogeneity or lineage-scarcity axis, and the same per-condition full-feature LFC-RMSE design. Related class-level and other-model work was not treated as an exact match. Novelty therefore did not disqualify the candidates, but it cannot rescue failed closure gates.

## 9. Provenance and integrity

- Original frozen files were re-hashed before resumed outcome access. Later contracts were hash-frozen before their specified untouched files were opened; hashes are recorded in [frozen_state_hashes.txt](results/frozen_state_hashes.txt).
- ST-HVG official score files were retained with their official LFS manifest.
- For ST-SE `eval_best` and `eval_last`, 15 selected prediction/result files per checkpoint were downloaded and verified against official repository size and LFS SHA-256. Five observed-DE files per checkpoint were not duplicated: the official ST-SE tree hashes exactly matched the already verified ST-HVG copies.
- Full-feature row accounting was 2,274,000 DE rows per context except 2,272,000 for PANC-1, matching 1,137 released targets in four contexts and 1,136 in PANC-1.
- Each final analysis verified five contexts per eligible target, one hash partition per compound, no missing required confirmation fields, and 268 confirmation compounds.
- All audit scripts compile in the saved workspace-local environment. The final artifact manifest records hashes and sizes for specifications, scripts, results, plots, and acquisition manifests.
- No SPECTRA tool was needed during continuation; no stored finding, sibling audit, completed v2 result, manuscript result, or pending queue was read or used.

## 10. Remaining gaps

- The S-phase axis has plate-split and full-QC measurement replication but no truly independent single-cell atlas with the same five contexts and released per-cell S-score definition. Bulk CCLE/CMP cannot measure within-context cell-state heterogeneity.
- Only five held-out contexts exist in the released zero-shot panel, making context-shape gates discrete and sensitive to individual lines; this limitation was not waived.
- `eval_last` is a related checkpoint, not an independent model/data confirmation surface.
- No additional public, same-checkpoint Tahoe drug-dose blocks exist beyond the complete released output used here, so the frozen error-spending increment cannot be executed without new public data.
- A preexisting unused probe, `acquisition/tahoe_cell_line_rows.json`, contains an HTTP 503 HTML response despite its extension. It was excluded from JSON validation and never entered an analysis; it is retained unchanged as failed-acquisition provenance.

## Final closure call

The audit is complete and closes negative at the model level: **no prospective input-side axis was certified as a STATE generalizability failure under every frozen criterion**. The strongest unresolved scientific signal is that ST-SE condition-level error increases on average with baseline S-score heterogeneity after controls, but its context curve is not sufficiently ordered to support the frozen generalizability claim.
