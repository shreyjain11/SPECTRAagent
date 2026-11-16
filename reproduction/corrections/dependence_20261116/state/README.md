# STATE Reactome pathway-set similarity: endpoint uncertainty

This corrects `state-featured/test-03`. All 13 notebook code cells were rerun in a fresh kernel after the correction plan was saved. The original notebook and execution receipt are retained. No model inference or fine-tuning was performed.

The original percentile interval sampled individual condition rows separately within the low and high endpoints. Genes recur across contexts, and some genes occupy different levels in different contexts. The corrected interval samples the union of canonical genes; every row belonging to a selected gene receives the same multiplicity across both endpoints and contexts. The statistic remains the original row-weighted high-minus-low mean overlap@N. It does not give equal weight to gene means or sample the endpoints separately.

All four intervals use the original 2,000 draws and seed 7. All 8,000 draws had observations in both endpoints. The corrected means, individual records, scores, features, level assignments, curve tables, descriptive trends and plotted figure are byte-identical to the original-code replay. Only the uncertainty calculation and its interpretation changed.

| Subset | Representation | L2 − L1 | Previous row-bootstrap 95% interval | Corrected gene-bootstrap 95% interval |
|---|---|---:|---:|---:|
| Jurkat/RPE1 | HVG | 0.096027 | 0.075669–0.116034 | 0.073875–0.119098 |
| Jurkat/RPE1 | SE | 0.084276 | 0.065020–0.104101 | 0.062477–0.105951 |
| HepG2/K562 | HVG | 0.117516 | 0.095315–0.138392 | 0.092833–0.141170 |
| HepG2/K562 | SE | 0.098334 | 0.078418–0.118068 | 0.075171–0.121410 |

The confirmation subset has 1,753 annotated rows and 1,222 genes per representation; 99 genes span both endpoint levels and 531 recur across contexts. Discovery has 1,567 annotated rows and 1,147 genes; 100 span both levels and 420 recur across contexts.

The printed conclusion now uses the annotated L1–L2 contrasts and their gene-cluster intervals, rather than the generic L0–L2 table. Both confirmation intervals remain above zero. This is a two-level association within the fixed Jurkat/RPE1 panel. L0 contains unannotated genes and is not a third informative similarity level. The correction does not establish a three-level degradation curve, a universal relationship, causality, full protocol completion, or a new prospective confirmation. The training reference remains reconstructed. The representation-specific intervals are not simultaneous intervals across representations.

## Evidence

- `PLAN.json` and `PLAN.sha256`: the exact plan frozen before numerical replay.
- `original.ipynb.gz`, `previous-execution.json`: exact original artifacts.
- `original-replayed.ipynb.gz`, `before-execution.json`, `before.log`: fresh-kernel replay of the original code.
- `after-execution.json`, `after.log`: actual corrected execution, host, Python, timing, command and authentic execution counts.
- `input-manifest.json`: all 22 consumed public input URLs, sizes and hashes; cache bytes were independently reverified.
- `environment.json`: actual execution package versions.
- `before/` and `after/`: full-precision original and corrected tables and notebook-generated receipts.
- `before-after-contrasts.csv`: direct numerical comparison.
- `per-condition-results.csv.gz`: the unchanged individual records, losslessly compressed.
- `after/bootstrap_gene_membership.csv`: each gene's endpoint row counts and score sums.
- `after/bootstrap_draws.csv`: every draw and its endpoint row counts, including the representation and subset.
- `verification.json`, `verification.log`, `verify.py`: independent reconstruction of all draws by duplicating actual full gene blocks, source-data checks and before/after equality checks.
- `registration.json`: integration fields for the shared correction receipt generator. Integration changes metadata and HTML only; the scientific execution is recorded above.

The first attempt to start the original replay was blocked by the sandbox's local kernel-socket restriction. Its failed receipt and log are retained under `sandbox-kernel-failure-*`. The subsequent original and corrected executions both completed successfully with local kernel permission.

To reproduce the corrected notebook, run the repository's notebook runner with any empty working directory and an optional verified input cache:

```sh
STATE_PRIMARY_INPUTS=/path/to/cache PYTHONHASHSEED=0 \
  python reproduction/inline/execute_notebook.py \
  reproduction/inline/state/state-featured/test-03.ipynb \
  --cwd /path/to/empty-working-directory --timeout 600
```

The notebook contains all custom analysis code and downloads/checks its declared public inputs. `execute.py` records the exact local execution used for this correction; `verify.py` records the local paths of the original and corrected replay outputs used in its independent check.
