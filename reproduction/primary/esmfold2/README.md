# ESMFold2 primary workflows

The twelve notebooks preserve the original accepted, discarded and exploratory axes, their individual measurements, main curves and recorded agent decisions. `traceability.json` connects each axis through data → processing → axis definition → levels → evaluation → curves/diagnostics → original decision. It is a workflow inventory, not a new scientific verdict.

## Run a notebook

Use Python 3.11 or later. From the repository root:

```sh
python3.11 -m venv .venv-reproduction
.venv-reproduction/bin/python -m pip install -r reproduction/primary/esmfold2/requirements-acquisition.txt
.venv-reproduction/bin/python reproduction/primary/execute_notebook.py reproduction/primary/esmfold2/notebooks/test-01.ipynb --cwd reproduction/primary/esmfold2
```

The default run expands the small offline artifact package, checks original file hashes, and replays the archived measurements with original processing functions. It needs no model download or GPU. Main curves are already saved in the notebooks; running restores the larger candidate galleries and original-source displays omitted from the compact saved outputs.

To execute reference acquisition, feature reconstruction, current-model inference and the original axis analyses, append `--original-workflow`, or set `RUN_ORIGINAL_WORKFLOW=True` in the notebook. This route requires CUDA hardware and the separate model environment described in `ENVIRONMENTS.txt`. It downloads the exact model revisions and reference bytes identified by the manifests. Do not enable it merely to view the saved curves.

All twelve notebooks share `reproduction/transformers-5.22.2` inside this package, including model weights, environment, references and per-panel results. Set `SPECTRA_ESMFOLD2_WORKSPACE` to change that location. Per-axis analyses are separate. Existing results are reused only when their input, model-setting and scientific-program receipts match. Missing or changed files stop the chain; new analyses never silently fall back to archived results.

## Included inputs

`original-artifacts.zip` is a deterministic, content-addressed archive: 301 unique objects restore 584 required paths (406 recovered original files and 178 prior replay inputs). `artifact_manifest.json` records every path, size and SHA-256. `bootstrap.py` verifies both archive and extracted bytes and refuses to overwrite changed originals. It uses only the Python standard library and no network.

Original scripts and tables retain their exact bytes, including recorded historical remote paths. Those paths document the original runs. The portable helpers supply local paths; neither SSH nor the original machine is required for the documented replay. No installed Biohub source, model weights, raw structure/MSA collection, cache, or duplicate validation result tree is included.

## Validation and limits

`WORKFLOW_VALIDATION.json` records all twelve axis dispatch checks on explicitly staged retained inputs/results. `CURVE_REPLAY_VALIDATION.json` compares 19 tables containing 1,285 curve rows against their original counterparts. `WORKFLOW_GUARD_VALIDATION.json` checks changed-input propagation, missing/stale-input failure and fresh cross-panel sample selection. `PACKAGE_VALIDATION.json` records clean-package bootstrap and portability checks.

Full bulk downloads, raw-feature reconstruction over the full cohort and fresh model predictions were not executed during this packaging task. The public current implementation uses pinned original folding/backbone weights. The completed conversion verified 2,658 native tensor keys and shapes; independent saved-value and prediction equivalence were not established. The original fork remains documented separately. Historical frozen levels, including the known flexible-axis boundary discrepancy, and original decisions remain unchanged.

The notebooks’ displayed mean intervals are labelled replay diagnostics. Original contrast intervals and controls are evaluated by the retained historical functions. Candidate names may recur across source panels, directions and stages; these are not counted as independent discoveries.
