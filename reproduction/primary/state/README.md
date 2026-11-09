# Original STATE primary analyses

These19 primary notebooks and the history notebook preserve the original accepted,
rejected and diagnostic entries. They rebuild processing, frozen levels, curves
and controls from the official STATE **released scored CSVs** used by the original
agent. No neural inference is needed to reproduce that original workflow.

From this directory, using Python3.11:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python state_inputs.py --offline
.venv/bin/python recovered_pipeline.py
.venv/bin/python ../execute_notebook.py notebooks/test-01.ipynb --cwd .
```

Select the virtual environment as the Jupyter kernel, or use the repository's
common notebook runner with that interpreter. Open
`notebooks/00-original-downloads-and-axis-history.ipynb` to see every tested
candidate screen and original disposition. Every individual notebook restores
and verifies its required inputs in the first cell; `.py` exports preserve code
cell order. Outputs go to ignored `computed/`, never to the original directories.
Cached stages are explicit; remove `computed/` to replay every calculation.

`payload_manifest.json` records the SHA256 of each bounded offline Git pack and
of every unpacked member. The packs separate official score-cache downloads,
historical annotation snapshots, and original comparison tables. Original code,
split TOMLs, ledgers, expected curves and decisions remain directly reviewable.
The bootstrap rejects a changed existing input rather than overwriting it.
`download_manifest.json` records58 exact public score/metadata URLs at pinned
Hugging Face revisions. `fetch_public_scores.py` can reacquire those same bytes;
old annotation snapshots are supplied because a current release would change the
historical analysis. No private storage address or server account is required.

The complete recovery inventory remains `original_manifest.json`; it includes
unused material intentionally excluded from this runnable package. The payload
manifest lists those exclusions. In particular, the unused all-species Reactome
file, paper PDF and native controller transcripts are not dependencies and are
not published here. The exact human annotation input is retained.

The original nearest-drug code has an unordered-set tie: tied names can differ,
while similarities, assigned levels and evaluated outcomes match. The regression
entry shows its original diagnostic instead of inventing a performance curve.
`traceability.json` links each axis to its inputs, processing, levels, score
origin, curve/diagnostic and historical decision. `PORTABLE_VALIDATION.json`
records checks performed on this packaged copy, separately from saved historical
notebook outputs.
