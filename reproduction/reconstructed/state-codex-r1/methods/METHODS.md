# STATE Codex r1 reconstruction — methods and source evidence

This directory contains reconstructed methods, unchanged surviving original scripts, and software tests. Scientific execution is performed on exxact05 by run_analysis.py after original-source feature and DE-score receipts validate. Actual completion is established by computed/analysis/analysis_receipt.json; older software-only receipts or aggregate drafts do not establish scientific reproduction. No coefficient or result is chosen to match the report.

## Runnable components

- `original/01_build_prospective_axis.py` through `04_analyze_frozen_axis.py`: unchanged original bytes, matched by the final artifact manifest.
- `reconstruct.py`: feature/condition constructors, original regressions, batched original compound bootstrap, paired target/reference contrasts, quintile-indicator adjustment, dose/context sensitivities and compound-balanced SPCs.
- `run_analysis.py --root ROOT`: consumes hash-verified actual DE reductions and source-derived features; writes distance, S-phase, lineage and control results plus CCLE and HVG discovery sensitivities. Every default run verifies scientific cache identities; missing/stale stages fail rather than using historical summaries.
- `sources.json`: 65 input records with URLs, expected sizes/hashes, origin notes, and ten actual local `_results.csv` paths. Repeated real-DE inputs are the same bytes shared by checkpoint analyses, not independent samples. `cmp_member` pins the extracted CSV as well as its archive.
- `SOFTWARE_TEST_RECEIPT.json`: latest completed remote software-test results, method hashes and library versions. The current test script includes13 checks on explicitly synthetic fixtures. A receipt applies only when its method hashes match the current files. Software tests are not scientific result reproduction; actual analysis has its separate completed receipt.

## Exact original sources

1. Sanger Cell Model Passports archive: `https://cog.sanger.ac.uk/cmp/download/rnaseq_all_20220624.zip` (940,707,972 bytes; SHA256 `2af6fd33a16c5c3d48a8d78976f54b4a09fcf0bac4102317b621f24d7bdca39a`). Member `rnaseq_tpm_20220624.csv` (257,466,286 bytes; SHA256 `54514510ffa03f3050e3787ab3d7f5a4d677068c4ed1a20177a7b57381d3a5bb`). Original download event362 and extraction event377.
2. Final DepMap23Q4 expression: `https://ndownloader.figshare.com/files/43347204` (449,782,440 bytes; SHA256 `d8e6eb9152c164e9bae49741fd46f5d4fd14c0d298c2a6de5d0996cb6cd3a6f8`). Model metadata: `https://ndownloader.figshare.com/files/43746708` (530,469 bytes; SHA256 `6b77a73209ce3faaa7442dbd947d8e08ddcb08b538c36fe820163f9cff321341`). Original event461. Earlier20Q3 downloads were superseded: do not accidentally use them.
3. Official `arcinstitute/ST-HVG-Tahoe` revision `ca6b751972493f8448e3256d1340ae70ad43e1e7`, `zeroshot/state_generalization_zeroshot_X_hvg/eval_best.ckpt/`: five contexts × original observed/predicted DE tables and result CSVs. The reconstruction downloads and verifies the full original DE/result files on exxact05; the score-stage receipt records all15 newly calculated context/checkpoint tables. Original verified file manifest is recovered in sibling `recovery/original_handoff/supporting/acquisition/official_scores/verified_manifest.json`.
4. Official `arcinstitute/ST-SE-Tahoe` revision `03b1971d7cc93a7535fd2e957c6948dba267378b`, `zeroshot/state_generalization_zeroshot_X_state/{eval_best.ckpt,eval_last.ckpt}/`. Final integrity checks specify every prediction/result hash and verify that observed DE bytes equal the HVG originals. Both checkpoint releases are acquired on exxact05 and used by the actual DE reduction stage; no inference is required.
5. Tahoe `metadata/obs_metadata.parquet`, original100,648,790 rows/96 row groups, 2,293,981,573 bytes, SHA256 `e51b24f3666f5f433c59ff01dd6fa33934627091455e89d929f2c1ddc87401fe`. Original event813 used the official dataset through an HF mirror. The exact original byte hash must match even when fetching a pinned repository URL. It contains `cell_name`, `drug`, `drugname_drugconc`, `plate`, `S_score`, `pass_filter`, and the count/QC fields; expression matrices are not needed for these input-side features.
6. Official zeroshot `cell_type_onehot_map.pkl` enumerates the Tahoe panel for the atlas mapping. Native event521 used the successful HF-client copy under `hf_st_hvg_tahoe2`, **not** the failed48-byte `acquisition/state_tahoe_cell_type_onehot_map.pkl`. `sources.json` uses the official pinned-revision 517,889-byte file (SHA256 `44bbc9823979ec02a336d62651cf6918e3f6ce162e20b42f86eb06d7e872e20a`, supported by the sibling public API inventory).

The ten local result CSVs are under `output/primary-notebook-recovery-2026-11-08/state/original/state_generalizability_20260602_single_controller/hf_cache/hub/models--arcinstitute--ST-{HVG,SE}-Tahoe/snapshots/<revision>/zeroshot/<run>/eval_best.ckpt/`. Full absolute paths are in sources.json. They provide overlap/Pearson/MSE summaries, but **those fields cannot substitute for the report's DE-derived full-feature log2-fold-change RMSE**.

## Reconstructed seven-stage chain

**Acquisition:** download and hash-verify the above public bytes on exxact05, sharing observed-DE files only after identity checks. `inputs/DOWNLOAD_RECEIPT.json` records acquisition progress/completion; the completed remote copy is packaged at `execution_evidence/download_receipt.json`. `computed/scores/score_receipt.json` records the completed actual DE reductions.

**Processing and metrics:** use original04's exact target/feature alignment checks. For each released DE row take log2(fold_change); STATE RMSE is sqrt(mean((pred−real)^2)), identity-reference RMSE is sqrt(mean(real^2)), and nDE counts observed fdr<.05. Join the per-target official result table and per-cell metadata counts by exact target string/context. Prefer full-QC cell count; use all-cell count when full count is zero.

**Axes:** original01 maps the panel to DepMap23Q4 metadata, excluding five held-out contexts. CMP is log2(TPM+1); choose2000 training-context high-variance genes, standardize by training mean/sample SD, calculate RMS Euclidean distance and median of five nearest training-context distances. CCLE intersects the selected genes and uses the documented parental HepG2 proxy. Preserve the original code's actual gene selection; the report's phrase “protein-coding” does not add an independent filter absent from that code. S-phase uses pandas sample SD of original `S_score` for untreated `drug == DMSO_TF` cells in the five contexts. Original native events911/922 establish the all-cell and odd/even plate operations. Full-QC-only replication is separate. Lineage is `-log(1+n)` where n counts mapped training contexts sharing the held-out DepMap Oncotree lineage; training counts are calculated from the original mapping, never hardcoded from the desired answer.

**Levels and selection:** retain five-context distance/S-phase order, and tied lineage levels. Parse target as the original single `(drug,dose,unit)` tuple. Normalize parent compound by lowercase and deleting non-alphanumerics. First16 SHA256 hex digits modulo10 assign0–2 discovery,3–9 confirmation. Retain target conditions in all five contexts, with compounds represented at two or more doses. Compare resulting counts to historical379 compounds/1136 targets total;268 compounds/804 targets/4020 rows in confirmation without modifying eligibility to force agreement.

**Original results:** compute from the downloaded official output tables; no fresh inference is needed. Preserve checkpoint representation: HVG eval_best for distance/discovery, SE eval_best for S-phase confirmation, SE eval_last for lineage follow-up.

**Curves and controls:** original within-target centering removes target intercepts; OLS has no extra intercept, with parent-compound clustered inference. Continuous controls are identity RMSE, log1p(nDE), log1p(observed cell count). SPC first averages doses within compound/context, then weights compounds equally. Final report requires paired compound bootstrap samples for target-reference slope differences. The reconstruction uses the same compound multiplicities across target/reference fits and computes dose and leave-one-context sensitivities.

**Historical decision:** keep the report's distance negative, S-phase strong-regression/failed-ordering negative, and lineage failed-stability/qualified-prospectivity negative. Bootstrap or replay differences must be reported rather than changing a frozen rule to reproduce the verdict.

## Explicit unresolved details

- Initial original04 uses axis sample mean/SD over **all released score rows before completeness filtering**. Missing final S-phase/lineage scripts may or may not use that same population. `build_condition_table(..., axis_z_scope=...)` requires an explicit choice and records it. Do not select a policy by searching for the closest published slope.
- Final S-phase bootstrap count10000 is documented; the final continuation random seeds and precise resampling order are not recovered. `analyze_axis(..., seed=..., reps=...)` has no defaults. Point estimates are deterministic given inputs/policy; finite-bootstrap CI endpoints need not be byte-identical without historical seeds.
- The surviving initial04 computes target and reference bootstraps with different seeds and subtracts them. Final report explicitly says **paired** resamples, so blindly rerunning initial04 does not implement the final contrast. The new code follows the final documented method and is labelled reconstructed.
- Recovered distance control_sensitivities.csv identifies the historically named matching procedure: all4020 rows and exactly eight categorical controls, effect_q_1 through effect_q_4 and cells_q_1 through cells_q_4. The runner therefore uses these indicators in original within-target regression, without continuous covariates for this sensitivity. Original cutpoint scope is absent; the fixed reconstruction takes quintiles within the analyzed partition, shared across contexts. No coarsened matching, dropping observations or weighting scheme is added. Dose/leave-one-context analyses retain the full-panel axis scale.
- Final report records full released feature panels and exact counts, which must be checked against acquired inputs. No aggregate result is expanded into synthetic per-condition observations.

## Minimal invocation after verified real inputs exist

```python
from reconstruct import original_scoring, s_phase_features, lineage_features, build_condition_table, analyze_axis
m = original_scoring()
counts = m.extract_cell_counts(original_obs_parquet, output_dir / 'cell_counts.csv')
s_axis = s_phase_features(original_obs_parquet)
s_axis = s_axis[s_axis.subset == 'all']
conditions, eligibility, released = build_condition_table(
    se_best_directory, shared_real_de_directory, counts, s_axis,
    axis_z_scope='all_rows',  # explicit inheritance from initial04; continuation not verified
)
result, curve = analyze_axis(conditions, seed=20260714, reps=10000)
# The seed above is a declared reconstruction seed, not an asserted original seed.
```

For exact distance construction invoke unchanged original01 with the original successful cell map, DepMap23Q4 Model/expression files and extracted CMP member. Never substitute stored five-point means for the individual condition table.

## Fixed full-run policy (recorded before scientific execution)

All axes inherit original04 all-released-row axis standardization and seed20260714. Each bootstrap uses10000 parent-compound resamples, the documented final S-phase count. The same count/seed are used consistently for all reconstructed analyses; this does not assert the unrecovered continuation seed was identical. Target and identity comparisons share exact resampling multiplicities. Numerical comparisons against published estimates/curves are emitted without altering these choices.

`run_analysis.py` reads three actual DE reduction sets (hvg_best,se_best,se_last), each with five condition score tables and the copied original results CSVs. The completed build_scores receipt pins original input identities, original scoring code and new output hashes. Feature receipts similarly pin original metadata/atlas inputs and new feature tables. Retained source bytes may be absent only when such completed, still-valid computations exist; archival summary tables are never accepted as substitutes.

Outputs: computed/analysis/{distance,s_phase,lineage}/{per_condition_scores.csv,compound_eligibility.csv,analysis.json,spc_table.csv,spc.png,matching_weights.csv,matching_strata.csv}. The historical filename matching_weights.csv now contains all original units and their eight quintile indicators, **not matching weights**. `analysis.json.partitions` contains discovery, confirmation and all; each has raw/adjusted/reference fits, paired intervals, dose/leave-one-context estimates and the categorical sensitivity. Additional files cover independentCCLE (including exact contexts), HVG discovery for later axes, and original baseline-feature discovery correlations. Controls has the combined condition records and all sensitivity estimates. `historical_comparison.csv` compares only after calculations; `analysis_receipt.json` hashes sources, methods, upstream receipts and every scientific output.

## Observed reconstruction agreement

All four notebooks completed full default recalculation on exxact05. All 30 original context-level curve means agree to numerical precision; the 58 comparisons with declared tolerances pass. Quintile-control estimates differ: distance −0.1278523 versus historical −0.12478; S-phase +0.1069716 versus +0.10494. Original indicator names and counts survive, but the exact bin-estimation population, cutpoints, tie handling and per-row assignments do not. `recovery/QUINTILE_METHOD_EVIDENCE.json` records the evidence search. The missing binning details are a limitation; they are not established as the sole cause of these differences. The policy was not tuned to the recorded estimates.
