# PR workflow traceability review

Scope: all 143 analysis entries. The question is whether a reader can follow the original data source and processing, axis definition, levels, results, curves or diagnostics, and historical decision. This review does not reassess protocol compliance or impose a new scientific study.

| Coverage | Entries | Meaning |
| --- | ---: | --- |
| Primary workflows packaged | 44 | Exact retained inputs or verified bootstrap, original code, visible decisions and per-axis evidence chain. Full new ESMFold2/CONCH model runs remain unexecuted. |
| Original records/computations missing | 58 | Publicly downloadable evidence and aggregate-display cells execute, but do not reconstruct the missing original individual-record computation. |
| Additional calculation replays packaged | 32 | Public checksum-verified archives and automatic preparation now supply the retained numeric inputs. Upstream execution checks match these notebooks; remaining historical gaps stay explicit. |
| Source workflows reconstructed | 9 | STATE Codex r1/r2 public inputs, feature construction, individual error calculation, curves and controls executed on exxact05; reconstructed continuation choices and numerical differences are explicit. |

**The four primary investigations have been integrated, and the additional 32 calculation replays now have connected public inputs. This does not mean all 143 original workflows have been reconstructed.** The 58 evidence/aggregate-only entries still lack original per-record computations or measurements. Successful execution of their display cells does not fill those gaps.

## STATE Codex r1 source reconstruction

The [four executable notebooks](reconstructed/state-codex-r1/README.md) replace the preferred evidence-only implementations for this investigation. Each default Run All recalculates derived stages, starting from 55 verified public source files (11.55 GB). All 28 code cells executed on exxact05. The workflow reduced 34,104,000 released gene-level rows across 15 context/checkpoint tables, rebuilt axes and levels, and calculated the original curves and controls.

All 30 historical context-level curve means match to numerical precision. The 58 comparisons with declared tolerances pass. Two quintile-control estimates remain different: distance −0.12785 versus −0.12478 and S-phase +0.10697 versus +0.10494. The original eight indicator names survive, but their exact bin assignments do not; this uncertainty is documented and no binning policy was selected to force agreement. Continuation random seeds and standardization inheritance are also explicit reconstruction choices. The [comparison table](reconstructed/state-codex-r1/computed/analysis/historical_comparison.csv) retains every difference.

The original 143 public-bundle execution records remain unchanged and bound to their legacy notebooks. The new source reconstruction has separate per-notebook execution receipts and package hashes.

## STATE Codex r2 source reconstruction

The [five executed notebooks](reconstructed/state-codex-r2/README.md) cover all 12 original candidates plus the A10 reference comparison. All 35 code cells ran on exxact05. They calculate individual released-score analyses, source-built axes, references, curves and controls, and the eligibility/design diagnostics that stopped unscored candidates. The original computational helpers were absent; reconstructed implementations follow the retained frozen definitions and disclose unresolved choices.

Dose coefficients and principal distance estimates closely reproduce. The A9 mitochondrial analysis does **not** numerically reproduce: its reconstructed raw coefficient is +0.02526 versus the historical −0.00044. Metadata/QC aggregation remains uncertain; no condition is removed merely to recover an old result. The missing 879-gene mapping and 1,536 partial reconciliation rows from unfinished A2e work remain explicitly unavailable. No unperformed confirmation curve is invented. See [status and limitations](reconstructed/state-codex-r2/RECONSTRUCTION_STATUS.json) and [methods](reconstructed/state-codex-r2/methods/METHODS.md).

## Primary workflows

| Investigation | Entries | Evidence chain |
| --- | ---: | --- |
| ESMFold2 | 12 | [All seven stages](primary/esmfold2/traceability.json) |
| STATE | 19 | [All seven stages](primary/state/traceability.json) |
| CONCH | 6 | [All seven stages](primary/conch/traceability.json) |
| AlphaMissense | 7 | [All seven stages](primary/alphamissense/traceability.json) |

The original decision remains tied to the original measurements. New results are separate. Prescoring rejections preserve the diagnostic that caused the decision. Released STATE scores and AlphaMissense predictions are the original starting points; fresh target inference is not a missing requirement for them.

## Additional investigations

The independent [nonprimary review](NONPRIMARY_REVIEW.json) was updated for upstream commit `55886b7`. Every previously missing input-file example now maps to a published archive member in [the data catalog](data.json) and model inventories. [Automatic preparation](prepare_inputs.py) verifies and materializes these inputs, and [the upstream execution report](execution.json) records checks for all 143 notebooks. The review matched all 99 nonprimary notebook hashes to their error-free execution records. Independent HEAD checks returned HTTP 200 and matching declared sizes for all four public archives; the bulk downloads and scientific executions were not repeated. The [complete per-axis review](traceability_review.json) covers all 143 entries.

| Investigation | Original calculations/records missing | Public-input-backed calculation replay | Source reconstruction |
| --- | ---: | ---: | ---: |
| esmfold2-codex-r1 | 4 | 0 | 0 |
| esmfold2-codex-r2 | 6 | 0 | 0 |
| esmfold2-opus-r1 | 4 | 0 | 0 |
| esmfold2-opus-r2 | 4 | 0 | 0 |
| esmfold2-kimi-r2 | 0 | 2 | 0 |
| esmfold2-kimi-r1 | 0 | 3 | 0 |
| state-codex-r1 | 0 | 0 | 4 |
| state-codex-r2 | 0 | 0 | 5 |
| state-opus-r1 | 0 | 4 | 0 |
| state-opus-r2 | 0 | 5 | 0 |
| state-kimi-r1 | 0 | 4 | 0 |
| state-kimi-r2 | 3 | 0 | 0 |
| conch-gpt-r1 | 7 | 0 | 0 |
| conch-gpt-r2 | 7 | 0 | 0 |
| conch-opus-r1 | 0 | 3 | 0 |
| conch-opus-r2 | 0 | 3 | 0 |
| conch-kimi-r1 | 1 | 0 | 0 |
| conch-kimi-r2 | 1 | 2 | 0 |
| am-gpt-r1 | 5 | 0 | 0 |
| am-gpt-r2 | 4 | 0 | 0 |
| am-opus-r1 | 0 | 3 | 0 |
| am-opus-r2 | 0 | 3 | 0 |
| am-kimi-r1 | 6 | 0 | 0 |
| am-kimi-r2 | 6 | 0 | 0 |

The CONCH Kimi r2 stain entry remains an aggregate pilot display: its pilot table is now downloadable, but original per-image stain-factor outcomes were not retained. Its other two entries have calculation code and connected public numeric inputs.

Historical scientific issues, such as the AlphaMissense Opus coordinate-join error and the ESMFold v1/v2 distinction, remain documented. Correcting an old conclusion or conducting an unperformed confirmation is not part of this traceability criterion.

## Validation boundary

The primary package reports record clean-package extraction/execution and the checks actually run. ESMFold2 additionally matches 19 original curve tables spanning all 12 axes and tests changed/missing-input propagation. CONCH preserves the original discovery and follow-up scoring code, features and logits. Raw bulk downloads and fresh neural scoring were not launched for those primary packages. The later STATE Codex r1 reconstruction did download and verify its complete public source set and execute all derived calculations on exxact05; its original workflow uses released predictions.

The repository validator checks records and artifact links/hashes. The upstream execution report distinguishes running retained notebook calculations or evidence displays from recovering missing historical measurements. Its four archive-download checks and one empty-cache public-installation run are recorded separately. The 32 additional calculation replays should not be labelled fully reconstructed original workflows solely because they execute. The website/protocol remain unchanged.
