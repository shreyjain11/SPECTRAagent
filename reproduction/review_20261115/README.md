# Individual notebook review — November 15, 2026

The [combined ledger](all-143-entry-review.json) covers **all 143 entries in 28 investigations**, using the canonical IDs in [the reproduction index](../index.json). It preserves the full findings and metadata from each model's review; each entry's original review is under `review`.

| Model | Entries | Individual review | Additional notes |
|---|---:|---|---|
| ESMFold2 | 35 | [Ledger](esmfold2-entry-review.json) | [Prose corrections](review_esmfold.py) |
| STATE | 44 | [Ledger](state-entry-review.json) | [Report](state-review.md) |
| CONCH | 30 | [Ledger](conch-entry-review.json) | [Report](conch-review.md) |
| AlphaMissense | 34 | [Ledger](alphamissense-entry-review.json) | [Report](alphamissense-review.md) |

## What was checked

Each entry was reviewed for agreement among its dataset and split, axis and levels, model/version and scores, curve/uncertainty, and stated interpretation. Reviewers read prose, scientific code and saved results; repeated common functions were compared across each family, with differing branches checked separately. Markdown was corrected where spacing, copied descriptions or claims misrepresented the calculation. Scientific code and saved numerical/graphical outputs were preserved in this review.

This was **not a fresh execution of all 143 analyses**, a redownload of every input, or a recovery of the exact original audit chronology. A current reconstruction can be useful without being numerically identical to the historical run. Eligibility records are not performance experiments; internal partitions are not automatically external confirmation.

The [presentation comparison](presentation-independent-check.json) records code/output preservation and generated-page checks. The [browser layout record](browser-layout-checks.json) covers all 143 pages for headings, image loading, overflow and clipped code at the recorded viewport. These checks do not validate the scientific claims by themselves.

## Numerical checks actually performed

- **STATE:** [36 checks](state-numerical-checks.json), using retained condition tables for selected slopes, adjusted coefficients and contrasts. No fresh inference or bootstrap rerun.
- **CONCH:** [106 check groups across 30 entries](conch-numerical-checks.json), including source/error checks and arithmetic from printed tables: endpoint differences, class recalls/eligibility, correlations, odds-ratio transforms, tumor contrast and blur difference-in-differences. No image feature extraction, neural inference or bootstrap rerun. [Check script](check_conch_entries.py).
- **AlphaMissense:** [21 checks](alphamissense-numerical-checks.json): all 12 Kimi endpoint tables, six paired-gene tables, five depth correlations in each Opus run, 100 weighted-AUROC helper trials, and exact occupancy boundaries. [Check script](verify_alphamissense_saved_outputs.py).
- **ESMFold2:** individual source, saved-result and interpretation review for all 35 entries. For Kimi r2, the retained-coordinate scoring and downstream calculations were also rerun for 160 model predictions and 120 available template predictions. The [recalculated results](esmfold2-kimi-r2-coordinate-check.json) retain the pooled endpoint contrast and the inconclusive expansion endpoint. No new structure inference was run. [Check script](verify_esmfold_coordinates.py).

These counts describe different kinds of checks and should not be combined into a count of independently reproduced analyses.

## Issues still requiring care or new computation

- **STATE Kimi r1:** the pooled embedding statistic omits required normalization, and recurring genes complicate independence. The saved statistic remains visible with an explicit warning. It needs a dependence-aware recalculation before inferential use.
- **STATE Opus r2 test 05:** context adjustment treats categories as numeric codes, and the hash split is process-dependent. Stronger adjustment/holdout claims require explicit categorical indicators and a reproducible split. Primary STATE controls also contain redundant indicators and nonclustered uncertainty.
- **STATE Codex r1 test 04:** the first saved graph still has an incorrect printed x-axis label. Its actual variable is S-phase standard deviation. Adjacent prose identifies the mismatch; the graph was retained unchanged rather than silently altered.
- **AlphaMissense primary depth:** the extreme paired comparison contains one assay, giving a degenerate bootstrap interval. It is now described as descriptive, not an assay-general depth result. Several other endpoint/reference or within-gene comparisons remain unresolved.
- **ESMFold2:** the three Kimi r1 entries use **ESMFold v1**. Kimi r2's pooled endpoint does not establish independent confirmation in its expansion. Several proposed axes remain inconclusive within their measured cohorts.
- **CONCH:** current Opus r2 blur DiD is **0.240741**, distinct from the historical **0.219**. Tile-level uncertainty does not establish patient/site independence. Fresh inference still requires access to the official checkpoint. The retained GPT r1 test 07 output string `fixed50-per-level` is shown with corrected whitespace in the HTML; the saved output itself is unchanged.

The per-entry ledgers retain additional limits, including comparator coverage, mutable acquisition endpoints, cohort composition, reused observations and reconstruction differences. The revised explanations narrow claims where needed; they do not convert these limitations into completed experiments.

Run `python reproduction/review_20261115/consolidate_reviews.py` from the repository root to rebuild the combined ledger. The script asserts 143 unique canonical IDs, exact per-model coverage, and preservation of every source entry.
