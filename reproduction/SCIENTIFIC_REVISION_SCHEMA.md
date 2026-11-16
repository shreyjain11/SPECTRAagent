# Scientific correction evidence, version 1

This format records an executed scientific correction separately from an earlier
execution. It does not label the scientific conclusion as established. All paths
below are relative to `reproduction/`; files must be present locally. Artifact
objects contain `path` and SHA-256 `sha256`, and may include `bytes`.

## Current execution receipt

Keep the normal analysis ID, notebook/HTML paths and hashes, six sections,
result location, code-cell count and other integration fields. Set the current
`host`, `python`, `elapsed_seconds`, `executed_cells` and `errors` from the actual
execution. `completed: true` refers to the explicitly declared scope:

```json
{
  "execution_scope": "selected_cells_reexecuted",
  "scientific_revision": {
    "schema_version": 1,
    "scientific_reexecution": true,
    "mode": "selected_cells",
    "previous_execution_evidence": {"path": "...previous-execution.json", "sha256": "..."},
    "original_notebook_snapshot": {
      "path": "...original.ipynb.gz", "sha256": "...",
      "compression": "gzip", "notebook_sha256": "..."
    },
    "record": {"path": "...scientific-revision.json", "sha256": "..."}
  }
}
```

For a full execution use `mode: "full_notebook"` and
`execution_scope: "full_notebook_reexecuted"`. `executed_cells` is the number of
code cells actually executed now, not a count copied from the earlier receipt.
Selected execution must not claim `all_code_cells_executed` in `checks`.

Archive the exact earlier receipt and gzip the exact earlier notebook bytes
before editing. The uncompressed snapshot hash must match the earlier receipt's
notebook hash. This permits independent offline verification of every preserved
cell. Preserve any earlier presentation/scientific revision chain through the
archived receipt. Remove the new receipt's obsolete `presentation_revision` and
`presentation_note`; do not relabel the previous execution as a new one.
Legacy source-receipt pointers belong in the archived receipt, not as evidence
for the new execution.

## Scientific revision record

```json
{
  "schema_version": 1,
  "analysis_id": "state-codex-r1/test-04",
  "scientific_reexecution": true,
  "mode": "selected_cells",
  "reason": "Correct the axis label using the retained per-condition records.",
  "original_commit": "40-character commit hash",
  "original_artifacts": {
    "notebook": {"path": "inline/...ipynb", "sha256": "..."},
    "html": {"path": "inline/...html", "sha256": "..."}
  },
  "published_artifacts": {
    "notebook": {"path": "inline/...ipynb", "sha256": "..."},
    "html": {"path": "inline/...html", "sha256": "..."}
  },
  "original_code_cells": [],
  "published_code_cells": [],
  "executed_notebook_cells": [21],
  "changed_code_cells": [21],
  "executed_cell_evidence": [],
  "execution": {
    "host": "actual execution hostname",
    "python": "actual Python version",
    "elapsed_seconds": 1.2,
    "started_at": "2026-11-15T12:00:00+00:00",
    "finished_at": "2026-11-15T12:00:02+00:00",
    "command": "actual command",
    "driver": {"path": "...driver.py", "sha256": "..."},
    "log": {"path": "...execution.log", "sha256": "..."}
  },
  "inputs": [
    {"path": "...per_condition_scores.csv", "sha256": "...", "role": "Saved per-condition model scores and baseline S-phase SD", "rows": 123}
  ],
  "prerequisite_setup": {
    "script": {"path": "...driver.py", "sha256": "..."},
    "input_paths": ["...per_condition_scores.csv"],
    "description": "Restores the curve globals from these saved records before executing cell 21. Earlier notebook cells were not rerun."
  },
  "output_artifacts": [
    {"path": "...recomputed_curve.csv", "sha256": "..."}
  ],
  "dependency_scope": "The selected plot cell was rerun after restoring its inputs. Other cells retain their exact earlier sources and outputs."
}
```

Use `validate_scientific_revision.code_cells(book)` to generate both cell
manifests. These are ordered lists of `notebook_cell`, `execution_count`,
`source_sha256`, `outputs_sha256` and `cell_sha256`. Source hashes use joined UTF-8
source text; output and full-cell hashes use sorted-key compact JSON with
`ensure_ascii=False`. `executed_cell_evidence` is the published manifest filtered
to the actual executed indices. `changed_code_cells` is the actual list of code
cell indices whose full cell objects differ from the archived snapshot.

Selected execution cannot insert/remove/retype cells, and cannot change any
unexecuted code cell, output or cell metadata. Record the prerequisite setup
script and the consumed input paths even when they are part of the same driver.
Full execution must include every current code-cell index; `prerequisite_setup`
is optional in that mode. Both modes bind the actual driver, log, input files and
regenerated output artifacts to hashes. Regenerated notebook/HTML hashes are
recorded separately; avoid self-referential hashes of the record or receipt.

The validator checks artifact identities, the original receipt chain and the
declared execution scope. It does not infer that a log proves all possible
scientific dependencies were correct, nor execute the analysis itself. A
separate numerical review must check the calculations and interpretation.

## Selected cells executed directly in Python

An actual Python `exec` of visible cell source is recorded with
`execution.engine: "python_exec"`; it must not invent Jupyter execution counts.
This option is restricted to `selected_cells`. Each declared cell keeps
`execution_count: null` and has `metadata.direct_execution` containing
`engine: "python_exec"`, `completed: true`, exact `source_sha256` and
`outputs_sha256`, and timezone-aware `started_at` / `finished_at` timestamps.

For this engine, `execution.log` is a structured JSON artifact. It records the
actual `host`, `python`, `driver_sha256`, `full_notebook_reexecution: false`, and
`cells` entries with `notebook` (repository-relative, starting `reproduction/`),
`cell_index`, `source_sha256`, `outputs_sha256`, `before_outputs`, `after_outputs`,
`started_at_utc` and `duration_seconds`. The validator compares these against
the archived original notebook, current cell, metadata and executed driver.
Cell timing must fall within the recorded execution interval. The default
notebook review remains strict: null execution counts are accepted only for
explicitly declared direct-execution cells with this evidence.
