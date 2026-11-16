# Investigation reporting

A small presentation-only renderer for one executed notebook per tested axis. It does not execute, import or alter analysis code. Research notebooks and data stay outside this example directory.

```bash
python -m pip install nbformat nbconvert
python examples/investigation-reporting/report.py /path/to/sequence.json --validate-only
python examples/investigation-reporting/report.py /path/to/sequence.json --output /path/to/report
python -m unittest discover -s examples/investigation-reporting/tests -v
```

Open `report/INVESTIGATION.html`; `index.html` contains the same page. Each axis is a native keyboard-accessible disclosure box. Opening it shows the result, exact notebook PNG, data links, measurement-table downloads and notebook links. `INVESTIGATION.md` contains the short ordered list. Exported notebook pages link back to the investigation; wide code and tables scroll inside their containers.

## Input contract

All local paths are relative to the directory containing `sequence.json` and must stay within it. The output must be a separate directory. The `axes` array must match the complete declared ledger, `expected_axis_ids`, in both membership and order.

```json
{
  "title": "Investigation title",
  "scope": "What was tested, and whether this is a new investigation or a replay.",
  "expected_axis_ids": ["axis-01"],
  "axes": [{
    "id": "axis-01",
    "title": "Biological property tested",
    "performed": true,
    "notebook": "axes/01.ipynb",
    "execution": "axes/01.execution.json",
    "started_at": "2026-01-01T10:00:00Z",
    "finished_at": "2026-01-01T10:05:00Z",
    "sources": [{"url": "https://example.org/public-data", "role": "Public input data"}],
    "result": "A short statement of the measured comparison and its scope.",
    "curve": {"cell": 9, "output": 0},
    "curve_caption": "Unadjusted group means; the adjusted comparison is reported above.",
    "tables": [{"path": "results/curve.csv", "role": "Per-level measurements", "sha256": "FILE_SHA256"}]
  }]
}
```

`curve` indexes are zero-based and must identify an existing `image/png` code-cell output. The renderer copies those exact bytes; it never draws a substitute. Use `curve: null` when a performed test produced no curve. Use `performed: false` for an unperformed axis, with `notebook`, `execution`, timestamps and `curve` all null; `result` should explain what was not done. These cases are displayed differently.

`curve_caption` and `tables` are optional. Tables may be CSV, TSV, JSON or Parquet; an optional SHA-256 is checked before copying. Input inventories can be linked as JSON. Additional fields in the sequence are retained by its source file but do not change the report. If `predefined_plan` names a local JSON file, its `expected_axis_ids` must match and its timezone-aware `created_at` must precede execution. This is useful for a planned replay, not evidence that an exploratory history was preregistered.

## Execution receipt

Each performed axis needs a receipt bound to the exact executed notebook bytes:

```json
{
  "analysis_id": "axis-01",
  "notebook_sha256": "NOTEBOOK_SHA256",
  "started_at": "2026-01-01T10:00:00Z",
  "finished_at": "2026-01-01T10:05:00Z",
  "executed_cells": 6,
  "completed": true,
  "errors": 0,
  "engine": "nbclient"
}
```

The receipt timestamps must match the sequence. Optional `executed_cell_indices` must cover the notebook's code cells in order. Every code cell needs an execution count, or explicit source/output-bound `metadata.direct_execution` when the receipt engine is `python_exec`. Such direct-execution metadata uses `completed: true`, the SHA-256 of joined UTF-8 source, and the SHA-256 of outputs serialized as sorted-key compact JSON with `ensure_ascii=False`.

The validator checks exactly six numbered `## 1.` through `## 6.` sections, code in every section, all-code execution coverage, no saved error outputs, notebook/optional-table hashes, declared-axis coverage/order, timezone-aware chronology, contained paths and HTTPS source links. Overlapping execution windows are disclosed, not reordered. `render-manifest.json` records exported notebook, curve and table hashes and the original curve cell/output indexes.

These checks establish artifact consistency. They do not independently authenticate a supplied execution receipt, verify every scientific claim, or prove that public URLs remain available. The tests use only tiny synthetic notebooks in temporary directories; no research data or generated pilot outputs are committed here.

## Pilot check — 2026-11-15

Tested with two existing STATE analyses from commit `d3cd8dcdd5e61011876010d9e55391229140bfdd`: Reactome support, followed by GO Molecular Function support. Both notebooks were fully executed in clean kernels (13 and 11 code cells) in a predefined replay order. An independent check recomputed all 50 curve points and both gene-clustered regression comparisons, verified the exact notebook PNGs and downloads, and resolved all 28 local HTML link appearances. The four displayed public source URLs responded without authentication. Desktop, narrow-layout, keyboard expansion and notebook-return navigation were checked.

This was a reporting-format test with released scores and reconstructed reference membership, not fresh discovery, model inference, historical reconstruction or independent replication. The rendered pilot and its data remain outside the static repository.
