# PR workflow traceability review

Scope: all 143 analysis entries. The question is whether a reader can follow the original data source and processing, axis definition, levels, results, curves or diagnostics, and historical decision. This review does not reassess protocol compliance or impose a new scientific study.

| Coverage | Entries | Meaning |
| --- | ---: | --- |
| Primary workflows packaged | 44 | Exact retained inputs or verified bootstrap, original code, visible decisions and per-axis evidence chain. Full new ESMFold2/CONCH model runs remain unexecuted. |
| Original records/computations missing | 67 | Publicly downloadable evidence and aggregate-display cells execute, but do not reconstruct the missing original individual-record computation. |
| Additional calculation replays packaged | 32 | Public checksum-verified archives and automatic preparation now supply the retained numeric inputs. Upstream execution checks match these notebooks; remaining historical gaps stay explicit. |

**The four primary investigations have been integrated, and the additional 32 calculation replays now have connected public inputs. This does not mean all 143 original workflows have been reconstructed.** The 67 evidence/aggregate-only entries still lack original per-record computations or measurements. Successful execution of their display cells does not fill those gaps.

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

| Investigation | Original calculations/records missing | Public-input-backed calculation replay |
| --- | ---: | ---: |
| esmfold2-codex-r1 | 4 | 0 |
| esmfold2-codex-r2 | 6 | 0 |
| esmfold2-opus-r1 | 4 | 0 |
| esmfold2-opus-r2 | 4 | 0 |
| esmfold2-kimi-r2 | 0 | 2 |
| esmfold2-kimi-r1 | 0 | 3 |
| state-codex-r1 | 4 | 0 |
| state-codex-r2 | 5 | 0 |
| state-opus-r1 | 0 | 4 |
| state-opus-r2 | 0 | 5 |
| state-kimi-r1 | 0 | 4 |
| state-kimi-r2 | 3 | 0 |
| conch-gpt-r1 | 7 | 0 |
| conch-gpt-r2 | 7 | 0 |
| conch-opus-r1 | 0 | 3 |
| conch-opus-r2 | 0 | 3 |
| conch-kimi-r1 | 1 | 0 |
| conch-kimi-r2 | 1 | 2 |
| am-gpt-r1 | 5 | 0 |
| am-gpt-r2 | 4 | 0 |
| am-opus-r1 | 0 | 3 |
| am-opus-r2 | 0 | 3 |
| am-kimi-r1 | 6 | 0 |
| am-kimi-r2 | 6 | 0 |

The CONCH Kimi r2 stain entry remains an aggregate pilot display: its pilot table is now downloadable, but original per-image stain-factor outcomes were not retained. Its other two entries have calculation code and connected public numeric inputs.

Historical scientific issues, such as the AlphaMissense Opus coordinate-join error and the ESMFold v1/v2 distinction, remain documented. Correcting an old conclusion or conducting an unperformed confirmation is not part of this traceability criterion.

## Validation boundary

The primary package reports record clean-package extraction/execution and the checks actually run. ESMFold2 additionally matches 19 original curve tables spanning all 12 axes and tests changed/missing-input propagation. CONCH preserves the original discovery and follow-up scoring code, features and logits. Raw bulk downloads and fresh neural scoring were not launched as part of this PR integration.

The repository validator checks records and artifact links/hashes. The upstream execution report distinguishes running retained notebook calculations or evidence displays from recovering missing historical measurements. Its four archive-download checks and one empty-cache public-installation run are recorded separately. The 32 additional calculation replays should not be labelled fully reconstructed original workflows solely because they execute. The website/protocol remain unchanged.
