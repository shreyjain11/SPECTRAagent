# STATE Codex r1: four source-to-decision reconstructions

Open the executed notebooks or their HTML files in `notebooks/`. Each default Run All recalculates features, released-score errors and analyses from verified public source bytes, even if computed outputs exist. Existing source downloads are checksum verified before reuse. Explicit CLI --reuse-computed is available only when intentional reuse is desired; notebook defaults do not request it. Original public predictions are scored again from full-feature DE rows; no new neural inference is needed.

Use Python 3.11 and install `requirements-executed.txt` to match the executed environment (or the declared scientific requirements in `requirements.txt`) before running. From this directory:

```bash
python execute_notebook.py notebooks/01-state-codex-r1-distance.ipynb
```

The same command applies to notebooks02–04. A cold run downloads the source manifest's public files and uses CPU/disk resources; the executed reconstruction was run on exxact05. Source inputs are not stored in Git. The small computed outputs and receipts here preserve the completed reconstruction, while original reports/tables serve only as validation targets.

`methods/METHODS.md` and `computed/analysis/reconstruction_policy.json` distinguish recovered methods from explicit continuation reconstructions. Historical decisions remain historical. Differences are reported rather than tuned away. `traceability.json` maps the seven stages for all four entries; `notebooks/NOTEBOOK_VALIDATION.json` records actual execution and HTML export. Original code-only notebook exports and the original143 execution report remain available through each record's legacy implementation.
