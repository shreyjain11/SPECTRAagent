# STATE calculation corrections

These records correct STATE Kimi r1 tests 01–04 and Opus r2 test 05. The original notebooks and execution records remain available at commit `1d3b45b`; the correction preserves every unexecuted code cell and its saved outputs.

Kimi's pooled seen-minus-unseen difference is 0.117729 (95% gene-bootstrap interval 0.096873–0.138288). The pooled within-unseen embedding-norm correlation is 0.504528 (0.473704–0.533788). Each bootstrap draw carries a gene's observations together across contexts and recomputes ties. These replace the previous pooled Z/p calculations. They quantify association conditional on the three observed contexts, not independent-site confirmation. Context-specific adjusted embedding results remain inconsistent, so the raw pooled relationship does not establish a proximity mechanism.

Opus's context-adjusted partial correlations are HVG 0.147379 (0.113562–0.180705) and SE 0.126895 (0.095797–0.159755). Context is represented by indicator columns, and bootstrap draws retain recurring genes and refit all ranks and residualization. The two sensitivity halves now contain 956 and 955 genes, assigned by stable SHA-256 ordering; this split is retrospective sensitivity rather than prospective confirmation. Pooled-row p values were removed from the descriptive sensitivity summaries.

`PLAN.md` and its timestamp/hash receipt precede corrected calculations. `before_after_results.json` compares the estimates. `registration.json`, the frozen executed drivers, per-entry logs, input hashes and bootstrap draws record exactly which cells were rerun. `real_data_checks.json` verifies direct expanded-row resampling against the implementation on actual inputs; all 10,000 draws per estimate were finite. No model inference or fine-tuning was performed.

The exact consumed public inputs are included as compressed files. To replay the corrected cells in a checkout from the repository root:

```bash
python reproduction/corrections/scientific_20261115/state_kimi_opus/restore_inputs.py --work /tmp/state-correction-replay
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python reproduction/corrections/scientific_20261115/state_kimi_opus/execute_changed_cells.py --repository "$PWD" --work /tmp/state-correction-replay --part kimi
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python reproduction/corrections/scientific_20261115/state_kimi_opus/execute_changed_cells.py --repository "$PWD" --work /tmp/state-correction-replay --part opus
python reproduction/corrections/scientific_20261115/state_kimi_opus/check_corrected_calculations.py --repository "$PWD" --work /tmp/state-correction-replay
```

These commands update selected notebook outputs; they do not execute the entire notebooks. The original public-source acquisition and metric-generation code remains inline for a complete notebook run. Actual correction package versions are recorded in `kimi_execution.json` and `opus_execution.json`.
