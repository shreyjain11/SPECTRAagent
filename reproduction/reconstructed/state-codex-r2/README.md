# STATE Codex r2: source calculations and original decisions

The five notebooks reconstruct the original measured investigations and the input/design diagnostics for candidates that stopped before scoring. Default Run All performs source calculations for that notebook's group (`--force`). Downloads may be reused only after verification; saved derived tables are not the default calculation input.

| Notebook | Original candidates and evidence |
|---|---|
| [01 Administered dose](notebooks/01-state-codex-r2-dose.ipynb) | A7 original sign-error stop; A8 few-shot result; A10 zero-shot result and A10R same-example basal reference |
| [02 Cross-cell distance](notebooks/02-state-codex-r2-distance.ipynb) | A1a nearest-distance diagnostic; A1b source-built atlas distances, individual scores, references, controls and exact context permutations |
| [03 Expected magnitude](notebooks/03-state-codex-r2-magnitude.ipynb) | A2 discovery and disjoint-target eligibility; A2e original unfinished input-aggregation diagnostic |
| [04 Secondary axes](notebooks/04-state-codex-r2-secondary.ipynb) | A3/A5/A6 source input levels and dependency closures; separate A9 measured mitochondrial investigation |
| [05 Modality](notebooks/05-state-codex-r2-modality.ipynb) | A4 source assignment table and exact dataset/modality design-rank diagnostic |

Each has the same seven stages: acquisition, processing, axis, levels/eligibility, released scores, curves/controls/diagnostics, and historical decision. The executable helper code is displayed alongside actual outputs. Original reported values are used only for comparisons and attributed historical determinations.

## Running

Use Python3.11 on exxact05 for this execution. Set up a separate environment and run all five sequentially:

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python execute_all.py
```

Or run one notebook:

```bash
.venv/bin/python execute_notebook.py notebooks/01-state-codex-r2-dose.ipynb --cwd . --timeout 10800
```

The source manifest supplies pinned public URLs and hashes. Source data are not intended for Git; a cold run downloads about10.6GB of source data, plus space for the environment and extracted observations/results, and requires CPU resources. No new neural inference is required: the investigations consume official released STATE outputs, and source-level reference/error calculations are rebuilt where they were part of the original workflow. The pipeline also supports explicit receipt-verified reuse when run without `--force`; notebook defaults always request recalculation.

Successful execution produces HTML counterparts, `notebooks/NOTEBOOK_VALIDATION.json`, individual pipeline/stage receipts in `execution_evidence/`, and `requirements-executed.txt`. The exporter rejects unexecuted/error cells or missing required figures. Unscored original candidates intentionally have diagnostic tables rather than invented performance curves.

## Recovered definitions and reconstruction choices

The original frozen definitions, report, candidate ledger and retained summaries are under `originals/`. The computational implementation is reconstructed in `methods/`; original executable helpers were not recovered.

- The specific frozen A1 contract defines mean distance using **one minus Spearman**; the report's cosine wording conflicts with it. The retained sensitivity record identifies **Jurkat E6.1**, while the report calls it a gene-block sensitivity. The code follows the specific retained definitions and leaves those disagreements visible.
- Original count/QC aggregation details were not recovered. The chosen public Tahoe observation metadata and technical-plate control matching are explicit in receipts. The resulting adjusted estimates and A9 mitochondrial results need not equal the original helper's results. Comparisons report those differences; alternatives are not chosen to fit a target number.
- Reconstructed normalization, bootstrap seeds, tie handling and deduplication are recorded with each stage. The A2 residual-correlation transform is incompletely described, so labeled versions are shown without selecting one by its agreement with the report.
- The original A2e 879-gene mapping rows and 1,536-block partial reconciliation are absent from the surviving handoff. Their hashes/counts remain historical evidence. The cohort and inventory are rebuilt, but the unfinished biological analysis is not silently completed or supplied with synthetic measurements.

The original historical decisions remain attributed to the original agent. This package does not replace them with a new scientific verdict or claim exact numerical equivalence for every reconstructed detail.
