# STATE SPECTRA generalizability audit

Status: **complete; low-dose generalizability failure certified**

Audit date: 2026-07-15 to 2026-07-16 UTC  
Controller: `audit/scripts/controller.py`  
Primary repository revision: `da4178c930dc917dac6b56faf10a33e21bd8e905`

## Executive verdict

The audit certified a real input-side failure on administered drug dose. On an
untouched ST-HVG-Tahoe zero-shot checkpoint, mean signed-LFC Spearman fell from
0.4738 at 5.0 uM to 0.4417 at 0.05 uM. The frozen negative-log-dose slope was
-0.01692 Fisher-z per SD (95% drug-block CI -0.02539 to -0.00908), and remained
-0.01592 (-0.02380 to -0.00810) after held-out nDE and treated/control-cell
counts. The low-minus-high contrast was -0.03204 (-0.04880 to -0.01676).

The same-example fixed basal-expression reference was flat (+0.00173, -0.02195
to +0.02621). The frozen point-estimate gate placed STATE within the +/-0.02
"comparable" band (STATE-minus-reference -0.01866), although degradation was
established for STATE and not for the reference. Dose is retained as the
prospective experimental axis; weaker response magnitude/measurement floor is
the likely mechanism.

The priority cross-cell-line distance axis was separately rejected on a
powered prospective test. Expected perturbation magnitude remained a strong
discovery candidate, but its original same-atlas confirmation was structurally
untestable in the released four-context tables.

## Audit integrity and acquisition

The SPECTRA protocol was requested first. No other SPECTRA tool was called, no
stored SPECTRA run or artifact was read, no pending-queue submission was made,
and no parallel agent was used. One persistent local controller records
resource provenance, freeze events, target access, and candidate decisions.

Pinned public resources include:

- STATE source at `da4178c930dc917dac6b56faf10a33e21bd8e905`;
- cell-eval at `9fec2dbfe46288ce9ba5aad6667f8f2c3224e0b1` and cell-load at
  `9ba45e59f6f8117bb7a21371ad38d67175586d53`;
- ST-SE-Replogle `e324967ff4cea5ec199e29bcbb5c1f00e5b9d69c` and
  ST-HVG-Replogle `bb6a9562cbbf1fd152df14cc53b4cc7517c77175`;
- ST-SE-Tahoe `03b1971d7cc93a7535fd2e957c6948dba267378b` and
  ST-HVG-Tahoe `ca6b751972493f8448e3256d1340ae70ad43e1e7`;
- DepMap 24Q4 expression/model metadata, Human Protein Atlas cell-line RNA,
  official Replogle-Nadig exports, Tahoe-100M/State-Tahoe-Filtered input data,
  and the exact official split TOMLs.

Machine-readable resource origins, versions, hashes, timestamps, licenses where
available, and derivations are in `audit/manifests/provenance.json`; controller
events are in `audit/logs/controller_events.jsonl`.

## A1: frozen cross-cell-line distance

Frozen contract SHA-256:
`d440a75833ce5dfba1f9cc341b7813366e6d7fe80f28258365abc4b3540cc99f`.

The feature was computed without target scores: cosine distance of each held-out
cell line's DepMap 24Q4 baseline expression from the equal-gene panel mean of
the other three STATE training contexts, over 18,979 common genes. HPA provided
an independent input-side ordering check. The initial nearest-context form had
only two symmetric values and was rejected prospectively; the panel-mean form
produced four strictly ordered levels:

| Level | Context | DepMap distance | STATE-SE mean rho | Reference mean rho | STATE-HVG mean rho |
|---:|---|---:|---:|---:|---:|
| 1 | K562 | 0.18046 | 0.10064 | 0.17459 | 0.12639 |
| 2 | Jurkat | 0.18355 | 0.10225 | 0.19466 | 0.17563 |
| 3 | HepG2 | 0.19475 | 0.14875 | 0.24528 | 0.15035 |
| 4 | RPE1 | 0.19575 | 0.07321 | 0.24944 | 0.21182 |

The HPA ordering exactly matched the four-level DepMap order (rank correlation
1.0; leave-one-gene-block sensitivity 0.8). The target set contained 638
perturbations complete in all four contexts, exceeding the precomputed target
of 263. Inference used 10,000 perturbation-block bootstrap draws and the signed
Spearman correlation of predicted versus real log-fold-change over 2,000
features.

The primary STATE-SE distance coefficient was **+0.00364 Fisher-z per distance
SD** (95% CI +0.00052 to +0.00687), opposite the degradation hypothesis. The
exact four-context one-sided permutation p-value was 0.583. The adjusted
coefficient was +0.00698 (+0.00301 to +0.01092) after true effect RMS, nDE,
perturbed-cell count, and mapped-control count. ST-HVG replication was also
positive: +0.02094 (+0.01675 to +0.02509). Although RPE1 was 0.02743 raw-rho
below K562, the full curve was nonmonotonic; that isolated endpoint is not
reported as a distance-axis failure.

The frozen model-independent reference was the equal training-context real
effect vector for each perturbation, never using the held-out outcome. It also
improved with distance (+0.03746, +0.03267 to +0.04220). Because STATE did not
degrade, the corrected reference gate was not invoked.

## A2 discovery and same-atlas confirmation gap

After the powered A1 negative, discovery on disjoint training-panel summaries
showed that expected perturbation magnitude was strongly related to STATE
performance (training effect-residual correlation 0.705; weakest-to-strongest
quintile mean rho 0.021 to 0.278). This was treated only as nomination, not
confirmation.

The frozen A2 confirmation contract
`47a96614261e23341cfabb9c606013e44790685a5e0760a03bafe7672ee71982`
excluded all 638 discovery perturbations and required each candidate in the
target plus every other training context. Among 1,385 disjoint released
candidates, zero met that four-context rule. No outcome test was performed and
the rule was not relaxed. The ledger records a resource gap requiring a
source-independent checkpoint/dataset.

## A2e: external Tahoe confirmation attempt

The external confirmation transports the mechanism from Replogle genetic
perturbations to Tahoe chemical perturbations and a separately released
ST-HVG-Tahoe few-shot checkpoint. The five held-out contexts are C32, HOP62,
HepG2/C3A, Hs 766T, and PANC-1. Intersecting their official test lists and
requiring complete 0.05, 0.5, and 5.0 uM triplets yielded 199 drugs, 597
drug-dose conditions, and 2,985 balanced context-condition units.

The drafted prospective feature was the equal-training-cell-line mean real-response RMS
for each drug-dose from the official Tahoe pseudobulk table, excluding all five
held-out contexts. Larger weakness is `-log1p(expected RMS)`. Five stable
equal-count levels run from strongest expected response (L1) to weakest (L5).
The fixed reference is the equal training-cell-line mean real LFC vector for the
same drug-dose.

The released ST-HVG metadata expose 62,710 gene names for a 2,000-column output
but omit the HVG mask/names. Exact equality between `X_hvg` and `log1p(X)` over
256 prospective training cells uniquely recovered 879 output-column/gene
mappings (mapping SHA-256
`fc87bd1a3d2e2f066d6f049d2b384994a022b295d3d31db7a046a966a44ecb1d`).
The remaining ambiguous zero-expression columns were excluded without target
access. The plan was to score STATE and the reference on exactly the same 879
genes using signed LFC Spearman, requiring at least 800 finite features per
unit.

The drafted primary inference was a context-fixed-effect regression of Fisher-z performance
on standardized weakness with 10,000 drug-block bootstrap draws. Confirmation
requires a negative coefficient with its 95% interval below zero and a negative
L5-minus-L1 raw-rho contrast. Required adjustments are held-out true effect
RMS, nDE, treated/control cells, genes/UMIs per cell, mitochondrial fraction,
context, and dose. If true magnitude absorbs the effect, the report will name
response magnitude as the driver and training-panel magnitude as its
prospective proxy.

The hosted pseudobulk table contains about 4.09 billion rows. Several bounded,
checkpointed input-only scans were attempted, including a block-indexed
reconciliation against 65,218 pseudobulk condition blocks. The released
metadata contained 65,243 candidate condition groups, while the hosted table
exposed 65,218 blocks; reconciliation stopped after 1,536 verified blocks and
did not yield a complete aggregate. The draft was therefore never frozen as an
A2e confirmation contract and the Tahoe target remained unread. The partial
block map and progress log are retained for reproducibility, but no A2e SPC or
biological result exists.

## Secondary axes and confounds

Sampling support (A3), dose displacement (A5), and representation/checkpoint
robustness (A6) were jointly specified before Tahoe target access under
SHA-256 `24ee9c8afcc3289b70c4cb58cdcdf151b59b1e5940dc20f11ed143fc3e8de67c`.
They depended on the same unfinished prospective input aggregation and were not
scored. They are closed as untested resource gaps rather than silently promoted
to evidence. No error-spending look was consumed for these axes.

Perturbation modality (A4) cannot be isolated causally by simply contrasting
the Replogle genetic and Tahoe chemical releases because modality is perfectly
confounded with dataset, context, preprocessing, and checkpoint. It is handled
as external transport of any A2e result, not misreported as a standalone
within-model modality coefficient. The candidate ledger records this as
non-identifiable in the available releases.

## A10: certified low-dose displacement

After the original dose analysis was small and directionally consistent but
inconclusive, the protocol's single rescue was frozen on an unread ST-HVG
zero-shot representation under contract SHA-256
`0fef61e0981ae75eaf988df4c1195adfc67115046ca4fab48549d9105ca65613`.
The panel contained 199 drugs with complete 5.0, 0.5, and 0.05 uM triplets in
five held-out contexts: 2,984 finite units (995, 994, and 995 by dose). No
outcome-dependent subgroup or level was selected.

| Dose | Units | Drug-block mean score | 95% CI |
|---:|---:|---:|---:|
| 5.0 uM | 995 | 0.4738 | 0.4616 to 0.4858 |
| 0.5 uM | 994 | 0.4399 | 0.4207 to 0.4570 |
| 0.05 uM | 995 | 0.4417 | 0.4254 to 0.4555 |

The primary slope, endpoint contrast, and adjusted slope all passed their
frozen directional gates. The result is not a cell-count artifact: adjustment
for real nDE and treated/control-cell counts changed the slope from -0.01692 to
-0.01592. Dose is experimentally assigned and known before outcomes. Because
nDE is a held-out response property, it is used only as a mechanism/control:
the most defensible interpretation is failure near the weak-response floor,
with administered dose as its prospective input-side proxy.

The model-independent reference addendum was frozen under SHA-256
`06cdb4e71e0b650970b77223424169afcdef33ae99f0071a6696e194d09fff32`.
It predicts gene-response ranks from negative DMSO basal-expression ranks and
uses no perturbed outcome to predict. On 2,982 identical examples its slope was
+0.00173 (-0.02195 to +0.02621). The preregistered point-estimate comparison is
"comparable," but only STATE showed a statistically established degradation.

## Novelty

The dated exact-match search and queries are in `audit/novelty_search.md`.
The closest adjacent result is a 2026 in-the-wild virtual-cell benchmark showing
broad context dependence and drops under stricter shifts; other work documents
strong systematic/mean perturbation effects. No exact match was found for the
pinned STATE checkpoint, frozen expected-magnitude axis, identical-example
reference, and controls. This is a bounded search result, not a claim that the
broad phenomenon is unprecedented.

## Remaining limitations and release gaps

- Only 879 of 2,000 ST-HVG output columns could be uniquely mapped from the
  incomplete release metadata without using target outcomes.
- The A2 same-atlas confirmation is structurally unavailable under its frozen
  complete-panel rule.
- The Tahoe fixed reference and prospective feature require a complete scan or
  a provider-side condition aggregate of the public pseudobulk table. The
  hosted interface did not provide a reliable complete block reconciliation;
  only the partial map and diagnostics are retained.
- The original training-context-mean Tahoe reference could not be materialized;
  the frozen executable reference is a weaker basal-expression mean-reversion
  comparator and should not be interpreted as a competitive benchmark.
- The A10 official score uses condition-specific significant real-DE genes;
  nDE adjustment mitigates but cannot eliminate measurement-floor effects.

## Closure verdict

**Closed: STATE has a certified low-dose generalizability failure.** The frozen
ST-HVG zero-shot test is powered, directionally consistent, control-robust, and
represents an experimentally assigned input-side shift. The fixed same-example
reference is flat but classified as comparable under the predeclared +/-0.02
point-estimate rule. A1 remains an honest powered negative; A2/A2e remain
resource gaps; failed checkpoint-specific discoveries are ledgered. Nothing
was submitted to the SPECTRA pending queue.
