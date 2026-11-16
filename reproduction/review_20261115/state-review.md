# STATE entry review

Reviewed all 44 STATE inline entries individually: source and cohort selection, axis definition, metric calculation, curves/controls, saved outputs and interpretation. Repeated identical source/setup code was inspected once per family. No complete notebook execution, new inference or all-input redownload is claimed.

The independent numerical check file contains 36 checks. All comparisons with stored coefficients agree within 1e-9. These checks use retained condition tables, not newly downloaded raw data.

## Corrections requiring computation or presentation work

- Kimi r1 test-03: pooled embedding Z lacks normalization. Its shared code/output also appears in tests 01, 02 and 04. The displayed 53.336430 statistic is not calibrated. A dependence-aware pooled analysis is needed; per-context values remain available.
- Opus r2 test-05: categorical context adjustment currently uses numeric codes; hash-based gene membership is process-dependent. Rerun these controls with explicit indicators and a reproducible predeclared split before making the stronger control/holdout claims.
- Codex r1 test-04: first saved graph x-axis is S-phase SD, not the four controls in its printed label. Adjacent correction was added; graph output remains unchanged.
- Primary multivariable controls (test-10, duplicated in test-09) use redundant subset/context indicators and row-wise rather than gene-clustered uncertainty. Descriptive coefficients can be read; stronger inferential use requires appropriate uncertainty and design checks.

## Per-entry findings

### state-featured/test-01 — STATE — Chemical similarity to training drugs

Checked: Inspected Morgan radius 2/2048 feature and context-specific metadata-minus-heldout reference construction. Checked rank-quintile assignments, released-score joins, HVG/SE curve and rejection.

Calculated result: HVG high-vs-low similarity means 0.517249 vs 0.529965; SE 0.509921 vs 0.523998. Proposed higher-similarity benefit is not supported.

Limitations: Reference membership is reconstructed rather than an exact recovered training manifest. Rank bins can split tied similarity values; condition composition is not dose/response matched.

### state-featured/test-02 — STATE — Dose represented in training

Checked: Checked three concentrations against reconstructed drug-dose reference combinations. Distinguished eligibility output from predictive degradation test; inspected unbalanced dose counts.

Calculated result: All three doses (0.05, 0.5, 5 μM) remain represented; this rejects dose-as-unseen-concentration, not a dose-performance effect.

Limitations: Displayed dose groups contain 1340,1339,995 condition rows per representation, not a balanced within-drug comparison.

### state-featured/test-03 — STATE — Reactome pathway-set similarity

Checked: Inspected alias canonicalization, Reactome set Jaccard, discovery quantiles and populated levels. Compared generic L0-to-L2 decision with annotated L1-to-L2 bootstrap.

Calculated result: Annotated-only confirmation gaps are HVG 0.096027 [0.075669,0.116034] and SE 0.084276 [0.065020,0.104101]; generic endpoint gaps include L0 and differ.

Limitations: Only two annotated levels are populated after tied cutpoints. Bootstrap resamples rows, not recurring genes.

Action: Markdown scope corrected; keep curve evidence but do not claim full three-level confirmation.

### state-featured/test-04 — STATE — Reactome mean

Checked: Read mean pathway-support calculation and frozen discovery quartiles. Checked confirmation means and generic endpoint decision separately by representation.

Calculated result: Confirmation L0-to-L4 gaps: HVG 0.104671; SE 0.079332.

Limitations: Endpoint contrast includes unannotated genes; the reference is reconstructed and confirmation reuses the benchmark.

### state-featured/test-05 — STATE — Reactome log-mean (REP)

Checked: Inspected mean log(1+pathway reference-gene count) feature and fixed levels. Checked L0 and annotated-only contrasts and the linked annotation/DE controls.

Calculated result: Confirmation L0-to-L4 gaps 0.127752/0.109374 (HVG/SE); annotated L1-to-L4 gaps 0.148154/0.128029.

Limitations: Support association remains after displayed controls but is observational; overlapping genes make row-bootstrap intervals narrower in scope than independent-cohort inference.

### state-featured/test-06 — STATE — Reactome minimum

Checked: Read minimum pathway-support feature and frozen binning. Checked confirmation endpoint direction and missing-annotation category.

Calculated result: Confirmation endpoint gaps: HVG 0.129601; SE 0.102355.

Limitations: Endpoints include L0; performance at every intermediate support level is not guaranteed by the endpoint decision.

### state-featured/test-07 — STATE — HGNC log-mean

Checked: Read HGNC-group memberships, same-context reference counts and log-mean support. Checked representation-specific confirmation curves.

Calculated result: Confirmation endpoint gaps: HVG 0.114834; SE 0.094445.

Limitations: HGNC grouping is an annotation-based proxy; same source benchmark and reconstructed reference membership.

### state-featured/test-08 — STATE — Gene-symbol prefix

Checked: Inspected alphabetical prefix extraction and reference matching. Checked how zero matching prefixes are encoded by generic level helper and inspected confirmation conclusion.

Calculated result: The feature counts reference genes sharing a name prefix, not curated gene-family membership.

Limitations: Legacy L0_no_annotation actually means no matching reference prefix.

Action: Markdown corrected; preserved legacy table label explicitly explained.

### state-featured/test-09 — STATE — Cell context and annotation counts

Checked: Read context-specific extreme comparisons and pathway-count quartile strata (minimum five examples per extreme). Checked all 30 retained strata and shared log-support regression.

Calculated result: All 30 eligible pathway-count strata show positive support contrasts.

Limitations: Quartile stratification is not exact matching; all results use the same benchmark observations. Shared regression duplicates subset/context information and uses row-wise uncertainty.

### state-featured/test-10 — STATE — Multivariable adjustment

Checked: Read OLS design and pseudoinverse, context/representation/subset indicators, annotation and log-DE covariates. Checked coefficient attenuation after response-strength adjustment.

Calculated result: Support coefficient declines from about 0.077876 to 0.028448 with log-DE adjustment across 6640 annotated condition rows.

Limitations: Subset is determined by context, so nuisance dummy columns are redundant. Standard errors do not cluster recurring genes; this limits inferential interpretation.

Action: Markdown corrected; clustered gene-aware uncertainty would require a new calculation if stronger claims are desired.

### state-featured/test-11 — STATE — Zero-shot pathway support

Checked: Read normalized support from other-context reference union. Checked few-shot frozen thresholds applied to zero-shot rows and per-representation endpoints.

Calculated result: Zero-shot high-minus-low endpoint gaps: HVG 0.067595; SE 0.043669.

Limitations: Protocol transfer uses the same benchmark, not a new experimental cohort; L0 contributes to endpoints.

### state-featured/test-12 — STATE — Ligand-family training support

Checked: Read explicit ligand-name family rules, train-reference counting, discovery/confirmation context assignments. Checked tied terciles and missing SE CD4 Memory confirmation coverage.

Calculated result: Confirmation contrasts are negative: HVG −0.056478; SE −0.038636. Two support levels are populated.

Limitations: HVG confirms across CD4 Memory/CD14 Mono; SE confirmation has CD14 Mono only. Name-based ligand families and coarse tied levels limit interpretation.

Action: Markdown corrected; negative conclusion unchanged.

### state-featured/test-13 — STATE — Reactome cross-ontology check

Checked: Inspected Reactome membership parsing, alias mapping, normalized log support and frozen discovery bins. Checked few-shot confirmation, zero-shot endpoint results and adjusted coefficient against displayed tables.

Calculated result: Few-shot endpoint gaps HVG/SE: (0.114425, 0.085313); zero-shot: (0.067595, 0.043669); adjusted support coefficient 0.0285501182.

Limitations: Normalized Reactome support; same released genes/outcomes as the primary pathway check. These are alternative features of the same benchmark, not independent experimental replications. Generic acceptance checks endpoints and populated levels, not every protocol requirement.

### state-featured/test-14 — STATE — HGNC_gene_group cross-ontology check

Checked: Inspected HGNC groups membership parsing, alias mapping, normalized log support and frozen discovery bins. Checked few-shot confirmation, zero-shot endpoint results and adjusted coefficient against displayed tables.

Calculated result: Few-shot endpoint gaps HVG/SE: (0.114409, 0.093496); zero-shot: (0.067848, 0.047095); adjusted support coefficient 0.0277922032.

Limitations: HGNC alias/group parsing changes feature coverage, not the outcome cohort. These are alternative features of the same benchmark, not independent experimental replications. Generic acceptance checks endpoints and populated levels, not every protocol requirement.

### state-featured/test-15 — STATE — GO_BP cross-ontology check

Checked: Inspected GO biological process membership parsing, alias mapping, normalized log support and frozen discovery bins. Checked few-shot confirmation, zero-shot endpoint results and adjusted coefficient against displayed tables.

Calculated result: Few-shot endpoint gaps HVG/SE: (0.161422, 0.13455); zero-shot: (0.087284, 0.056794); adjusted support coefficient 0.0145135408.

Limitations: Direct GAF memberships exclude NOT qualifiers; no ancestor propagation is applied. These are alternative features of the same benchmark, not independent experimental replications. Generic acceptance checks endpoints and populated levels, not every protocol requirement.

### state-featured/test-16 — STATE — GO_MF cross-ontology check

Checked: Inspected GO molecular function membership parsing, alias mapping, normalized log support and frozen discovery bins. Checked few-shot confirmation, zero-shot endpoint results and adjusted coefficient against displayed tables.

Calculated result: Few-shot endpoint gaps HVG/SE: (0.01429, 0.054462); zero-shot: (0.034752, 0.048388); adjusted support coefficient 0.00362478033.

Limitations: Adjusted support coefficient is smaller than the other ontology checks; do not treat strengths as interchangeable. These are alternative features of the same benchmark, not independent experimental replications. Generic acceptance checks endpoints and populated levels, not every protocol requirement.

### state-featured/test-17 — STATE — GO_CC cross-ontology check

Checked: Inspected GO cellular component membership parsing, alias mapping, normalized log support and frozen discovery bins. Checked few-shot confirmation, zero-shot endpoint results and adjusted coefficient against displayed tables.

Calculated result: Few-shot endpoint gaps HVG/SE: (0.121489, 0.09013); zero-shot: (0.081189, 0.054814); adjusted support coefficient 0.0065381858.

Limitations: Ontology annotations and outcome observations are shared with the benchmark. These are alternative features of the same benchmark, not independent experimental replications. Generic acceptance checks endpoints and populated levels, not every protocol requirement.

### state-featured/test-18 — STATE — WikiPathways cross-ontology check

Checked: Inspected WikiPathways membership parsing, alias mapping, normalized log support and frozen discovery bins. Checked few-shot confirmation, zero-shot endpoint results and adjusted coefficient against displayed tables.

Calculated result: Few-shot endpoint gaps HVG/SE: (0.103912, 0.126574); zero-shot: (0.034633, 0.034359); adjusted support coefficient 0.0186542044.

Limitations: Entrez-to-HGNC mapping leaves many unannotated records: 921/2145 confirmation and 2472/5759 zero-shot. These are alternative features of the same benchmark, not independent experimental replications. Generic acceptance checks endpoints and populated levels, not every protocol requirement.

### state-featured/test-19 — STATE — KEGG cross-ontology check

Checked: Inspected KEGG membership parsing, alias mapping, normalized log support and frozen discovery bins. Checked few-shot confirmation, zero-shot endpoint results and adjusted coefficient against displayed tables.

Calculated result: Few-shot endpoint gaps HVG/SE: (0.141454, 0.127841); zero-shot: (0.066405, 0.046664); adjusted support coefficient 0.0254595524.

Limitations: Unannotated records are about 990/2145 confirmation and 2647/5759 zero-shot. These are alternative features of the same benchmark, not independent experimental replications. Generic acceptance checks endpoints and populated levels, not every protocol requirement.

### state-codex-r1/test-01 — STATE Codex R1 — Basal transcriptomic distance

Checked: Read reference-only gene selection, CMP scaling and median five-neighbor distance, including all alias/proxy handling. Read balanced target eligibility, compound hash split and within-target OLS/compound bootstrap. Independently recomputed raw, adjusted and no-effect slopes from retained condition rows for all three partitions.

Calculated result: Confirmation raw STATE slope −0.032213; adjusted −0.150035; no-effect +0.163206. Distance-related worsening is rejected.

Limitations: Five contexts only; compound confirmation holds out drugs, not contexts. CCLE is an alternate expression measurement, with a declared parent-line proxy, not an independent outcome cohort.

### state-codex-r1/test-02 — STATE Codex R1 — Baseline S-phase heterogeneity

Checked: Read DMSO S-score SD extraction, QC/plate sensitivity and ST-SE eval_best selection. Checked raw/adjusted slopes and non-monotonic five-context curve. Independently recomputed within-target OLS slopes from condition rows.

Calculated result: Confirmation raw slope about +0.080561 and adjusted +0.095149, but ordered error means are non-monotonic.

Limitations: Rejection means no consistent graded worsening, not absence of association. Only five contexts; compound-resampling uncertainty does not create extra context replication.

### state-codex-r1/test-03 — STATE Codex R1 — Training-lineage scarcity

Checked: Read DepMap lineage-count join and negative-log1p scarcity; verified ST-SE eval_last paths. Checked adjusted fit, omitted-context reversal and representation sensitivity. Independently recomputed retained-row OLS slopes.

Calculated result: Raw confirmation +0.138244 and adjusted +0.032226; excluding HepG2/C3A changes adjusted sign to about −0.011958.

Limitations: Reference lineage counts are coarse and context-dependent; model checkpoint differs from S-phase entry.

### state-codex-r1/test-04 — STATE Codex R1 — Perturbation magnitude, DE count, cell count and dose

Checked: Read first plot construction, control-feature panels and three-axis raw/adjusted sensitivity code. Matched first plot x coordinates to S-phase SD and outcome means to ST-HVG predictions.

Calculated result: First graph actually uses S-phase SD 0.120724–0.328889; later graphs separately display magnitude, DE count, cell count and dose.

Limitations: First saved graph has a generic incorrect x-axis label; factual note is now placed immediately above. Controls are diagnostics, not independently accepted generalization axes.

Action: Adjacent Markdown correction saved; image/code preserved per instruction. A presentation-only rerender can correct the label.

### state-codex-r2/test-01 — STATE Codex R2 — Administered drug dose

Checked: Read exact five-context drug intersection, complete dose triplets, metadata aggregation, Fisher-Spearman response and cluster bootstrap. Compared raw A8/A10 dose and reconstructed A9 mito slopes to historical table; inspected paired-reference band.

Calculated result: A8 raw −0.0102968 with interval spanning zero; A10 raw −0.0169216 below zero. A9 reconstructed +0.025264 differs from historical −0.000442.

Limitations: Original metadata helper unavailable; reconstruction is not exact historical A9 replay. A10 difference interval [−0.042618,+0.004857] extends outside ±0.02, so point-estimate band is not equivalence.

Action: Existing disclosure retained and uncertainty/scope wording clarified.

### state-codex-r2/test-02 — STATE Codex R2 — Baseline cross-cell-line distance

Checked: Read DepMap/HPA gene intersection, RPE1 clone median and four-context distance. Read prediction/reference alignment and within-perturbation adjustment. Independently recomputed raw STATE, HVG, reference and adjusted STATE coefficients.

Calculated result: ST-SE raw distance slope +0.003635; adjusted +0.006983; context permutation p=14/24≈0.583. No robust worsening result.

Limitations: HPA changes feature ordering, not outcome cohort. All638 complete perturbations used in analysis; zero additional complete candidates follows from that construction.

### state-codex-r2/test-03 — STATE Codex R2 — Expected perturbation magnitude

Checked: Read other-context expected RMS, negative log transform and within-context levels. Independently recomputed residual Pearson correlations and context-adjusted weakness coefficient. Inspected 1385 disjoint-candidate eligibility rule.

Calculated result: Residual Pearson expected RMS +0.704952, weakness −0.700833; adjusted weakness slope −0.107892. No disjoint complete four-context confirmation.

Limitations: No remaining eligible complete cases is tautological after using the full intersection; it is not an exhaustive external-data search. Expected magnitude uses other-context observed responses, so it is not a wholly outcome-free biological feature.

### state-codex-r2/test-04 — STATE Codex R2 — Sampling support, prospective dose displacement and checkpoint sensitivity

Checked: Read sampling-count rank levels and metadata eligibility tables. Verified sampling, displacement and checkpoint candidates lack outcome curves in this entry; A9 crosslinks to test01.

Calculated result: Sampling levels use −log(1+treated count), not the administered-dose levels previously described. Three candidate entries remain unscored.

Limitations: Metadata/eligibility computations do not establish a performance result. A9 is scored in a separate entry and must not be described as unscored.

Action: Markdown corrected; no new outcome measurements invented.

### state-codex-r2/test-05 — STATE Codex R2 — Perturbation modality

Checked: Read dataset/modality indicator construction and rank calculation. Verified that no performance fit is substituted for a nonidentifiable design.

Calculated result: Dataset and modality columns are identical; design rank2 of3. Genetic perturbations only Replogle, chemicals only Tahoe.

Limitations: Without a crossed design no modality-only effect is identifiable. No Markdown correction needed.

### state-opus-r1/test-01 — STATE OPUS-R1 — Drug-target training coverage

Checked: Read companion annotations, official score identity joins, Replogle gene-panel target coverage and drug aggregation. Checked raw/partial correlations and size-matched placebo universe.

Calculated result: Positive zero-shot association; partial HVG rho≈0.120 p=.053 and SE≈.131 p=.034. Placebo uses union of panel/targets, not proven training universe.

Limitations: Fraction measures evaluation-panel target coverage; true training manifest is not recovered. Few-shot/representation strength differs; no generic model-wide conclusion.

### state-opus-r1/test-02 — STATE OPUS-R1 — Drug chemical novelty

Checked: Read self-excluded radius2/2048 Morgan novelty and drug-level quartiles. Checked 377-drug correlation and rejection.

Calculated result: rho −0.023133, p .6543; no supported chemical-novelty trend.

Limitations: Reference is other evaluated drugs, not verified training-drug membership.

### state-opus-r1/test-03 — STATE OPUS-R1 — Cell-context novelty

Checked: Read K562/RPE1 versus Jurkat/HepG2 binary group definition and paired gene averaging. Checked bootstrap group differences by representation.

Calculated result: Training-like minus other: HVG −0.012437; SE +0.030274, opposite directions.

Limitations: Group averages can contain one or two contexts; labels are declared groups rather than verified training exposure.

Action: Markdown corrected.

### state-opus-r1/test-04 — STATE OPUS-R1 — Intrinsic perturbation strength

Checked: Read observed-DE quintiles, per-condition aggregation, correlation and bootstrap for all12 panels. Confirmed observed effect diagnostic is outcome-derived.

Calculated result: All12 panel correlations positive, roughly .48–.95.

Limitations: This is response-strength association, not a prospective novelty axis or proof all confounding removed.

Action: Markdown corrected.

### state-opus-r2/test-01 — STATE OPUS-R2 — Gene-neighborhood coverage

Checked: Read GO-BP direct gene sets, self-excluded top5 Jaccard density, 1911-gene panel and quartiles. Checked zero-shot HVG/SE curves, context splits and alternative CC/pathway density results.

Calculated result: HVG level means .089572,.107774,.163516,.184552; SE .039735,.052237,.090249,.110838.

Limitations: Density uses evaluation genes, not verified training genes. CC/pathway checks reuse genes/outcomes and are not independent outcome replication.

Action: Markdown now states the actual neighbor pool and scope.

### state-opus-r2/test-02 — STATE OPUS-R2 — Chemical structure and mechanism coverage

Checked: Read chemical self-neighbor feature and row-weighted zero-shot quartile curve. Read mechanism-of-action grouping and mixed protocol scope.

Calculated result: HVG level means .239905,.236043,.242908,.246254; SE .136985,.134482,.143198,.152069. Weak/non-monotonic.

Limitations: Condition-weighted chemical plot differs from equal-weight drug plot; MOA diagnostic pools few/zero-shot without adjustment.

Action: Markdown corrected to row-weighted curve and pooled MOA diagnostic.

### state-opus-r2/test-03 — STATE OPUS-R2 — Drug-target or ligand functional density

Checked: Read maximum mapped target density and Parse mapped-gene density, annotation exclusions and family-specific correlations. Checked 264of379 drug mappings and1439of1458 Parse mappings.

Calculated result: Tahoe zero-shot correlations near0; Parse correlations near0; few-shot Tahoe weakly negative. Cross-family replication not established.

Limitations: Mapped subsets only; evaluation-panel density is not exact training exposure.

Action: Markdown corrected; null/inconsistent family results explicit.

### state-opus-r2/test-04 — STATE OPUS-R2 — Cross-context screen coverage

Checked: Read gene-wise unique-context count minus1 and zero-shot level aggregation. Checked 0..3 context-level curves by representation.

Calculated result: HVG .042052,.144082,.140516,.142362; SE .026789,.082805,.077439,.072818. Separation is0 vs any, not graded monotonic.

Limitations: Count describes evaluated screen coverage, not recovered training exposure.

Action: Markdown replaced with exact0..3 axis and binary boundary interpretation.

### state-opus-r2/test-05 — STATE OPUS-R2 — GO annotation count and perturbation strength

Checked: Read fixed-N, annotation-count, DE-strata, partial-rank, hash-half, density-trimming and context checks. Compared all printed robustness labels with precise selection/design operations.

Calculated result: Several conditional associations remain positive; controls do not support pure training-coverage or independent frozen-holdout wording.

Limitations: Numeric category-code residualization is not categorical context adjustment. Python hash(gene)%2 without fixed seed is not reproducible split membership. Density trimming does not remove named modules; above-median DE restriction does not remove all difficulty.

Action: Current Markdown limits claims and identifies the preserved printed labels; code/output intentionally unchanged.

### state-kimi-r1/test-01 — STATE Kimi R1 — Gene–cell-line pair exposure

Checked: Read retained unit-mean NPZ inputs, checkpoint identity, seen-pair membership, six delta metrics and fixed references. Checked seen/unseen differences in all3 additional contexts and pooled formula.

Calculated result: RPE1/Jurkat/HepG2 mean differences .117752/.118388/.117048; equal mean .117729.

Limitations: Benchmark contexts share genes; binary association not graded/no new experimental cohort. No fresh inference; checkpoint tensors supply only weight-norm diagnostic.

Action: Invalid Z/p explicitly flagged next to unchanged output; recompute a dependence-aware pooled inference before using it. Same shared output appears in all4 entries.

### state-kimi-r1/test-02 — STATE Kimi R1 — Graded gene exposure

Checked: Read count of other contexts E, order seen/E3/E2/E1 and K562 discovery curve. Checked direction of unseen-only rank trend and rejection.

Calculated result: UnseenE1/E2/E3 STATE mean delta correlations .373575/.355065/.314680; rho≈−.08099 with directional p≈.99414.

Limitations: Seen/unseen boundary does not rescue a rejected increasing-exposure trend.

Action: Invalid Z/p explicitly flagged next to unchanged output; recompute a dependence-aware pooled inference before using it. Same shared output appears in all4 entries.

### state-kimi-r1/test-03 — STATE Kimi R1 — Embedding-norm proximity

Checked: Read checkpoint one-hot mapping and L2 norm of pert_encoder.0.weight columns. Checked per-context raw correlation and adjusted coefficients. Independently reproduced erroneous53.33643 Z sum and demonstrated missing normalization without treating alternative formulas as valid inference.

Calculated result: Raw correlations .46559/.545164/.499152; RPE1 adjusted coefficient negative/nonsignificant, Jurkat and HepG2 positive.

Limitations: Weight norm is not geometric training proximity. Pooled contexts share genes and omitted-normalization Z/p are unusable.

Action: Invalid Z/p explicitly flagged next to unchanged output; recompute a dependence-aware pooled inference before using it. Same shared output appears in all4 entries.

### state-kimi-r1/test-04 — STATE Kimi R1 — Cell count per observation

Checked: Read perturbation-unit cell-count covariate, effect adjustment and seen-pair coefficients in4 contexts. Checked that cell-count diagnostic uses aggregated perturbation units, not individual-cell predictions.

Calculated result: Cell-count coefficients positive across all4 displayed contexts; adjusted seen-pair coefficients remain positive.

Limitations: Residual observational association is not elimination of every sampling/effect-size confound.

Action: Invalid Z/p explicitly flagged next to unchanged output; recompute a dependence-aware pooled inference before using it. Same shared output appears in all4 entries.

### state-kimi-r2/test-01 — STATE Kimi R2 — Perturbation exposure in any cell line

Checked: Read complete shared inference/cache procedure, source/checkpoint hashes and stored cache-reuse receipt. Read per-context support-cell count, ≥30-cell eligibility, control subtraction and binary bootstrap. Checked every context binary difference and three additional-context confirmation rule.

Calculated result: Seen−unseen differences K562 .152423, Jurkat .113748, HepG2 .054539, RPE1 .044790; saved intervals positive.

Limitations: Same Replogle dataset; positive binary separation is not monotonic graded support. Saved notebook executions reused shared verified predictions; no per-notebook fresh inference/fine-tuning.

### state-kimi-r2/test-02 — STATE Kimi R2 — Graded training-support count

Checked: Read shared inference/source procedure and zero/1–100/101–250/>250 support levels. Checked exposed-only trend in4 contexts and K562 graded means.

Calculated result: K562 positive-support means .233204,.214816,.183454 decrease; exposed-only correlation signs vary across4 contexts.

Limitations: No general monotonic support curve; binary and graded hypotheses differ. Shared predictions reused; no new experimental cohort.

### state-kimi-r2/test-03 — STATE Kimi R2 — Fixed-reference and embedding checks

Checked: Read same-gene other-context reference/fallback and equal-gene-context global reference. Checked per-context reference means, exposure contrasts and embedding-norm diagnostics.

Calculated result: STATE unseen performance lies below global reference in displayed contexts; relative exposure declines versus same-gene reference are not uniformly greater.

Limitations: Norm separation is not causal failure-mechanism proof. Inference cache reused and context observations share one experimental source.
