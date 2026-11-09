# STATE Codex round 2: reconstruction methods

These implementations reconstruct the original July 15–16, 2026 investigation
from surviving frozen contracts and public source bytes. The original private
analysis scripts were not present in the handoff. `originals/` preserves the
unmodified report, contracts, ledger, source manifest and retained summaries.
Historical results are comparison targets only and never inputs to fitted
coefficients, bin assignments or reference scores.

All scientific execution for this reconstruction occurs on exxact05. Python 3.11
and `requirements.txt` define the isolated CPU environment. Each computation uses
one BLAS thread. No model training or new inference is required: these original
Codex investigations evaluated released scored outputs and DE tables.

## Acquisition and reusable inputs

`acquire.py --root ROOT` resolves the exact recorded model commits and records
their immutable Hugging Face LFS SHA256/byte counts in `sources.json`. Original
DepMap, HPA and split-definition hashes are enforced. `--reuse OTHER_ROOT`
permits a symlink only after an existing object passes the same expected SHA256
and byte count. Otherwise it downloads the public object. Source data are never
replaced with historical aggregate results.

Replogle evaluation H5AD expression matrices are unnecessary. The
`observation_controls.py` helper reads only `obs` via HTTP ranges at the original
immutable URLs and saves the exact extracted tables with their own checksums.
The full H5AD LFS hash identifies the remote object; no receipt claims a local
full-file hash check of bytes that were not downloaded.

## Distance and expected magnitude

DepMap24Q4 and HPA provide the prospective expression axis. DepMap cell IDs and
the coordinatewise median of six RPE1 clones follow the frozen contract. Duplicate
gene symbols are collapsed by arithmetic mean. The lexical common-gene set is
fixed before evaluation. Average-rank Spearman distances to the other three
contexts are averaged. The original report's phrase "cosine distance" conflicts
with its frozen contract and exact retained numbers. The reconstructed DepMap
distances match the retained values to floating-point precision.

The original HPA sensitivity is explicitly Jurkat E6.1 substitution in both
the frozen contract and prospective summary. The report also calls its 0.8 rank
correlation a gene-block deletion sensitivity, for which no scheme survives.
The specific recorded Jurkat substitution is reproduced; no gene-block scheme
is invented. HPA numeric distances can differ slightly under the documented
duplicate-symbol aggregation, while its recorded ordering is reproduced.

Real and predicted DE tables supply signed log2 fold-change vectors over the
common 2,000 output features. Duplicate target-feature entries collapse by mean
log2 fold change. Nonpositive fold changes are excluded as nonfinite rather than
assigning an undocumented pseudocount. Primary eligibility is the intersection
of all four real/predicted context tables. The fixed reference averages the other
three contexts' real LFC vectors for the same perturbation. Expected response
magnitude is the mean RMS of those three vectors. Stable within-context sorting
by descending magnitude and perturbation name creates five equal-count levels.

Regressions use Fisher-z transformed correlations, population-SD axis scaling and
10,000 perturbation-block bootstrap draws with the retained seed20260715. Axis
scaling is fixed before bootstrap resampling. The exact24 context permutations
are enumerated. The adjusted-fit helper did not survive. The primary
reconstruction uses perturbation fixed effects, as supported by the frozen
paired-perturbation contract; pooled OLS is a separately labeled sensitivity.
Numerical agreement corroborates this reconstruction but cannot establish
the identity of the missing original helper. Controls are
log1p effectRMS, nDE, actual perturbed-cell count and unique mapped-control count.

## Dose, mitochondrial burden and fixed basal reference

The original split TOML determines the shared test conditions; require complete
0.05/0.5/5µM triplets per exact drug name after trimming external whitespace.
Released `de_spearman_lfc_sig` values are the original target metric. A8 uses
ST-SE few-shot best, A9 uses ST-SE zero-shot best, and A10 uses ST-HVG zero-shot
best. No checkpoint is selected by the reconstructed outcomes.

A8/A10 regress on standardized negative log10 dose with drug and context fixed
effects. A9's frozen aggregation specifies drug fixed effects for its raw fit;
its adjusted fit adds context, dose, nDE, support, genes and UMIs. The original
dose/mitochondrial bootstrap seed was not recovered;20260716 is an explicitly
documented reconstruction choice, with10,000 drug-cluster draws.

The original count/QC aggregation helper was absent. The reconstruction uses
actual Tahoe public observation metadata, aggregating all cells by context,
drug and dose, with each cell contributing once; matched DMSO controls are the
union of the condition's observed technical plates. The original provenance
names State-Tahoe-Filtered but describes a DuckDB query of an obs-metadata
parquet; the actual available public parquet is from Tahoe-100M and is pinned
to bytes already verified by the original round1 evidence. This resolution and
the all-cell choice are assumptions, not silently asserted exact old code.
Differences in adjusted/A9 results and eligible counts are shown explicitly.

A10R predicts negative ranks of log1p DMSO `reference_mean` from each official
real-DE table. It uses the same significant genes (FDR<.05), at least20 finite
features, and no perturbed outcome to predict. The perturbed fold change is used
only for scoring. STATE and reference slopes are fitted on identical eligible
examples. The frozen ±0.02 point-estimate comparison rule is retained.

## Honest unscored closures

A2 confirmation removes every discovery perturbation and checks four-context
availability from actual DE table identities. Its zero eligible count is a
computed eligibility result, not a missing outcome curve.

A2e's original Tahoe pseudobulk reconciliation never finished, and A3/A5/A6
depended on it. This package recomputes their cohort, available support/dose
features and level assignments, and shows the original source inventory. It
does not manufacture879-gene outcomes. The original879-row mapping and1536-block
partial map were not included in this handoff; their retained hashes/counts are
labeled historical evidence. A9 is a separate actual measured investigation and
is therefore calculated, despite appearing alongside these secondary closures.

For modality, the model/source assignment table is regenerated from pinned
release identities. A design-matrix check demonstrates that chemical modality
is identical to the Tahoe dataset indicator, so the contrast is unidentifiable.

## Execution and evidence

`run_pipeline.py --root ROOT --stage dose|distance|magnitude|secondary|modality
--force` recomputes the relevant scientific stages from source inputs. Notebook
Run All passes `--force` by default. Omitting it permits only explicitly labeled,
hash-validated calculation caches. Receipts record source hashes, method hashes,
output hashes, host and calculation policy. `test_methods.py` independently
checks the sufficient-statistic/within-cluster solver against direct OLS.
