# Notebook data and analysis records

`index.json` lists 28 investigations and 143 analysis entries. Each entry links to its notebook, code, input files and five sections: dataset/split, axis/levels, model evaluation, curve/uncertainty, and comparisons/controls/confirmation.

## Run a notebook

Use Python 3.12 or newer on Linux or macOS (execution was checked with Python 3.13). Until the PR is merged, use the public PR branch and install the requirements for the model you want to inspect:

```sh
git clone --branch manuscript-audit-registry https://github.com/shreyjain11/SPECTRAagent.git
cd SPECTRAagent
python -m pip install -r reproduction/materials/conch/requirements.txt
python reproduction/run_notebooks.py --analysis conch-opus-r2/test-01
```

You can also open the linked notebook in Jupyter and run its cells. Its first cell downloads the model's public input archive, verifies the archive and file hashes, and prepares the working directory. No GCP account, credentials or original run folder is needed.

The four archives are listed in `data.json` and available in the [public data release](https://github.com/shreyjain11/SPECTRAagent/releases/tag/notebook-inputs-2026-11-08-v1). They contain the retained sample tables, features, saved predictions, measurements, structures or images used by the supplied calculations. They are hosted as public GitHub release assets; the large files are not stored in Git. `sources.json` also lists the upstream datasets and code repositories.

To download the data before opening a notebook:

```sh
python reproduction/prepare_inputs.py --model state
python reproduction/prepare_inputs.py --all
```

Data are cached under `reproduction/.data/`. Set `SPECTRA_DATA_DIR` to use another disk. The full download is about 3.3 GB, with additional space needed for extraction and notebook outputs. Repeated notebook runs reuse the downloads.

Execution outputs are saved under `reproduction/.executions/`. Select another location with `run_notebooks.py --output`. To execute all notebooks, install `reproduction/requirements.txt`, then run `python reproduction/run_notebooks.py --all --workers 4`. Notebooks within a model execute sequentially.

## What the notebooks reproduce

The notebooks run the calculations supported by the retained records. Some reconstruct individual measurements and curves; others display recovered summaries or the record of a candidate that was never measured. Successful code execution does not recover missing historical measurements or establish a scientific conclusion.

The data downloads resolve access to the retained files. `reconstruction_notes` in each analysis, collected in `reconstruction.json`, still identify unavailable original samples, splits, annotations, predictions and design details. Those gaps have not been filled with newly generated results. An upstream dataset alone cannot recover a lost original experiment.

AlphaMissense's default replay uses the retained alignment-feature arrays on both macOS and Linux. The separate upstream build scripts are preserved; the original Linux MMseqs executable is not required for the replay or redistributed in the data archive. The documented coordinate-join error and OTU7A discrepancy remain explicit. ESMFold Kimi r1 retains its actual ESMFold v1 identity.

## Files and verification

- `inputs/<model>.json` lists each public archive member, size, hash and archive identifier. When provenance text was cleaned of original machine or private storage locations, its original hash is retained separately.
- `materials/` contains the supporting scripts and code-only notebooks. Notebook outputs are generated locally when executed.
- `samples/` contains compact identity/split/level tables. The full retained tables are in the public data archives.
- `code/<model>.json` identifies the supporting scripts and their public and original hashes.
- `execution.json` records the notebook execution checks, code hashes and environment. It distinguishes those checks from historical reconstruction.
- `validate.py` checks JSON records, notebook preparation cells, code hashes, archive mappings and sample tables. `run_notebooks.py` executes the notebooks; it does not assign scientific grades.

Model evaluation records distinguish fitting a comparator from fine-tuning the target model. Unknown original training events remain unknown. The website, protocol and hosted API are unchanged.
