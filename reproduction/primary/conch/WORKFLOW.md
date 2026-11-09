# Run the original CONCH investigation

Each of the six notebooks has one top-level switch, `RUN_ORIGINAL_WORKFLOW`.
Its default, `False`, replays and checks the archived measurements. Set it to
`True` to execute image acquisition, feature generation, axis freezing,
CONCH scoring, baseline fitting and curve generation. The six notebooks share
one run folder, so running the next notebook resumes verified completed stages.
Rerun mode stops on failure; it never substitutes archived target scores.

From the `reproduction/primary` directory, prepare Python 3.11:

```bash
python3.11 -m venv conch/.venv-notebook
conch/.venv-notebook/bin/python -m pip install -r conch/requirements_notebook.txt
python3.11 conch/setup_inference.py
```

The setup helper creates `conch/.venv-inference` with the original recorded
Torch 2.5.0/CUDA 12.4, torchvision 0.20.0, timm 0.9.16 and Transformers 4.57.6.
The remaining packages are pinned for this recipe; the complete historical
environment lock was not retained. Numerical feature/baseline processing uses
the separately pinned `requirements_reference.txt` environment, which has
already reproduced the historical axis assignments and baseline labels.
Setup does not change an existing environment. To use another prepared model
environment, set `CONCH_INFERENCE_PYTHON` to its absolute `bin/python` path.

Accept access to `MahmoodLab/conch` on Hugging Face and supply `HF_TOKEN` through
your environment or log in with the model environment's `huggingface-cli login`.
Do not place tokens in notebook cells. Select the desired GPU through
`CUDA_VISIBLE_DEVICES`. The original batch size is 128. The route checks for a
CUDA device before downloading model/data files. A deliberate CPU route is
available using `setup_inference.py --device cpu` and the notebook's
`ALLOW_CPU_INFERENCE=True`; it will be much slower and is not the original
hardware environment.

Run the full workflow and save its notebook outputs:

```bash
conch/.venv-notebook/bin/python conch/run_notebook.py conch/notebooks/01-conch-primary.ipynb --original-workflow --timeout 86400
```

The runner also accepts notebooks 02–06. Notebook 04 displays both follow-up
panels. All notebook curve cells consume the selected generated tables when
rerun mode is active. Without `--original-workflow`, the command performs the
explicitly labelled historical replay. `bootstrap_replay.py` first verifies and
expands the bundled compressed per-image results and reconstructed reference
matrix; no original workspace or data download is needed for this mode.
Raw-image checks explicitly report that they are skipped when those caches are
absent. They do not masquerade as newly executed pixel checks. In Jupyter, use the notebook environment
as the kernel and set the switch directly.

The expensive route acquires seven complete target-image Parquet shards
(3 CRC-VAL and 4 NONORM TUM), the approximately 802 MB checkpoint, and the small
source checkout. It reacquires the exact 1,800 selected reference images when their cache is absent.
The raw images are not stored in Git. It scores 7,180 discovery, 1,800 confirmation
and 4,000 expansion images. Reserve disk space for the shards, environments,
checkpoint and run outputs. This integration work did not perform those large
downloads or a new CONCH inference run.

## Exact sources and stage lineage

- Dataset `1aurent/NCT-CRC-HE`, revision
  `97765ecb14bf11ce7bb8779a1097d187844a67cb`. Exact seven shard names are in
  `original_pipeline.py`. Each full file is checked against that revision's
  upstream LFS SHA256. All 7,180 CRC image hashes and order must match the original
  identity columns before feature construction can proceed.
- CONCH source `https://github.com/mahmoodlab/CONCH`, commit
  `141cc09c7d4ff33d8eda562bd75169b457f71a62`. The source includes the local
  tokenizer and model configuration; no additional tokenizer download is used.
- Checkpoint `MahmoodLab/conch`, revision
  `f9ca9f877171a28ade80228fb195ac5d79003357`, `pytorch_model.bin`, checked against
  the pinned revision's LFS SHA256.
- Prompt file `prompts/crc100k_prompts_all_per_class.json`, set `0`, from the same
  pinned CONCH checkout. The receipt records its SHA256, templates, class names
  and order: ADI, BACK, DEB, LYM, MUC, MUS, NORM, STR, TUM.
- `run_original_stage.py` invokes the recovered original scripts unchanged.
  Its adapters redirect every streaming module to the same downloaded shards,
  rebuild prospective features with the original function, and verify the
  decoded image identity while scoring the frozen follow-up panels.
- Discovery axes freeze before scoring. The original six-level confirmation
  and ten-level expansion follow; expansion excludes the freshly built prior
  panel by stream key and decoded-image MD5. New scored tables feed the original
  baseline/analysis scripts, then the notebook plots.

`original_pipeline.py --plan` prints the stages without downloads or execution.
Fresh artifacts default to `generated/original-workflow`; set
`CONCH_RUN_DIRECTORY` to use a different run. Stage receipts hash their inputs,
outputs, recovered scripts, settings and environment. Incomplete stages rerun;
completed stages resume only when their recorded outputs still match. Scoring
logs are in `logs/`, individual results under `artifacts/`, and the final
`workflow_receipt.json` is required before a notebook can load generated curves.

The ten recovered original scripts are byte-for-byte unchanged and their hashes
are retained in `SOURCE_MANIFEST.json`. Selected original command/decision
records retain native-session line numbers; account-specific path prefixes in
these excerpts are replaced and that publication change is recorded. The full
private chat logs, image caches, checkpoints and environments are not included.
The original final report and agent decisions remain labelled as historical.
The recovered expansion report script contains fixed historical interpretation
sentences, so its generated prose is not treated as a new scientific decision.
New numeric curves and contrast statistics are displayed separately. This route
repeats the original screens and panels, including discarded screens; it does
not create a new confirmation study or claim independent-site generalization.

See `WORKFLOW_VALIDATION.json` for the checks actually executed and the boundary
between verified integration and the full model run, which remains unexecuted.


## Portable package contents

`PAYLOAD_MANIFEST.json` records both compressed and exact expanded SHA256 hashes
for the three complete retained scored tables, reconstructed reference matrix,
and reference-image identity manifest. These derived results are bundled once;
materialized CSV files and downloaded caches are ignored by Git.
`traceability.json` maps all six PR analysis IDs to data, processing, axis, level,
model, curve/diagnostic and historical-decision evidence. Notebook code exports
under `code/` preserve cell order and are syntax-checkable.
