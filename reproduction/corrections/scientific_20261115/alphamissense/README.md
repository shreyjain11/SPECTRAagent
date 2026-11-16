# AlphaMissense primary statistical correction

The fixed effective-depth endpoint has **one paired assay from one protein**. Its point estimate remains **+0.523308**, but the corrected code reports **no between-protein confidence interval** and **insufficient independent replication**. The plotted endpoint is an open point without an uncertainty bar. No bins, endpoint or eligibility thresholds were changed to obtain another result.

The shared DMS workflow in primary tests 03–07 now resamples **proteins**, carrying all assays of a sampled protein together. Curve means remain variant-count weighted; paired contrasts remain means of assay differences. It uses 5,000 replicates with seed 42 reset per statistic, so shared controls receive identical intervals across notebooks. Fewer than two proteins, or no empirical resampling variation, yields an unavailable interval. Two proteins is a mechanical minimum, not adequate evidence of population coverage.

| Comparison | Paired assays / proteins | Difference | Corrected 95% interval |
|---|---:|---:|---|
| Effective depth, depth0 → depth4 | 1 / 1 | +0.523308 | Unavailable |
| Occupancy, insertion → q4 | 44 / 40 | +0.214838 | [0.156994, 0.272468] |
| Occupancy within high depth, <0.5 → ≥0.9 | 19 / 17 | +0.151933 | [0.028273, 0.283765] |
| Separate coarse occupancy control | 61 / 52 | +0.124117 | [0.080353, 0.166844] |

The occupancy findings remain conditional associations in this cohort; they do not supply replication of the effective-depth endpoint. The dynamic-range diagnostic in test 07 retains its narrower experimental-spread interpretation. Clinical tests 01–02 use a separate protein/gene bootstrap, with at least 1,450/1,364 clusters per displayed level, and were not changed.

## What was actually executed

[Execution evidence](execution-evidence.json) records two reexecuted scientific cells per notebook: the per-assay statistic/aggregation/plot cell and the decision/export cell. Other code-cell objects, including their saved outputs, were checked against commit `1d3b45b` and preserved. Original notebooks and receipts are archived under `before/`.

The previous Broad per-assay files were not available locally. Inputs were rebuilt from three **already-public payloads**, using the same selected DMS records, coordinate checks and official AlphaMissense score join:

- [Frozen panel and official score subset](../../../primary/alphamissense/payloads/am-frozen-panel-and-score-inputs.tar.gz)
- [Original DMS members](../../../primary/alphamissense/payloads/am-original-dms-members.tar.gz)
- [Recorded alignment arrays](../../../primary/alphamissense/payloads/am-recorded-alignment-results.tar.gz)

The reconstructed input contains **270,572 variants, 72 scored assays and 63 proteins**. AlphaMissense/BLOSUM curve points, endpoint estimates and sample counts match the previous displayed values. Composition-file hashes also match. Recorded profile counts cause a small PSSM reference difference in test 06: the largest weighted curve change is about **0.0000073**. This is disclosed as a retained-profile route difference; the old per-assay files were not recovered byte for byte. No new inference, fresh clustering or external validation was performed.

The original [plan](PLAN-initial.md) was hashed before computation. The [retained-input amendment](PLAN-retained-input-route.md) identifies the reconstruction route; [the current plan](PLAN.md) also records the per-statistic seed policy.

## Reproduce and inspect

From the repository root, using an environment with NumPy, pandas, SciPy, Biopython, matplotlib, IPython and nbformat:

```bash
python reproduction/corrections/scientific_20261115/alphamissense/rebuild_retained_inputs.py /tmp/am-primary-retained
python reproduction/corrections/scientific_20261115/alphamissense/execute_selected.py /tmp/am-primary-retained
python reproduction/corrections/scientific_20261115/alphamissense/verify_correction.py
```

`execute_selected.py` writes the explicitly selected notebook cells and their outputs; run it in a working checkout. It does not execute earlier acquisition/alignment cells. The consumed input tables are in `inputs/`, regenerated statistical tables in `outputs/`, and before/after comparisons in `verification_tables/`. [Independent checks](verification.json) test single-protein guards, repeated-assay cluster resampling against explicit sampling, counts, endpoint arithmetic, and unchanged point-estimate scope. Execution/input/output hashes and timings are recorded separately from scientific interpretation.

Repeated large exports were deduplicated after byte-hash comparison. [The deduplication map](DEDUPLICATED_ARTIFACTS.json) resolves the filenames in raw calculation receipts to the canonical retained input/export files; no scientific records were discarded.
