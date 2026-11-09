ESMFold notebook collection

Open a test-NN.ipynb from its investigation folder and run all cells in order. Keep the adjacent inputs folder with the notebook. Each notebook contains its custom source acquisition, processing, axis construction, scoring, curves, controls and decision code.

The featured and Kimi notebooks calculate features and results from released per-target measurements or prediction coordinates. Their fourth section identifies this scope. The Codex and Opus model notebooks generate any predictions not already present in a verified sequence/model/settings-bound cache. A first model run downloads the pinned public weights and converts their tensor layout using the visible official converter code. Model inference needs an available CUDA GPU and can take sustained runtime.

MODEL_SOURCE_REVISION_EQUIVALENCE.json verifies that the pinned public source revisions have the same config/index/weight blob hashes as the sources used to build the executed converted checkpoint.

CPU_ENVIRONMENT.json records the environment used for released-score executions. MODEL_ENVIRONMENT.json records the separate model environment. Python3.11 is used. Third-party MMseqs2 and US-align acquisition/build commands are visible in the relevant cells; US-align compilation requires g++.

Environment setup (run from this collection directory):

  python3.11 -m venv .venv-cpu
  .venv-cpu/bin/python -m pip install -r requirements-cpu.txt
  .venv-cpu/bin/python -m ipykernel install --prefix .venv-cpu --name python3

For notebooks with fresh ESMFold2 inference, use a separate environment:

  python3.11 -m venv .venv-model
  .venv-model/bin/python -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu124
  .venv-model/bin/python -m pip install -r requirements-model.txt
  .venv-model/bin/python -m ipykernel install --prefix .venv-model --name python3

Execute an individual notebook with its matching environment, for example:

  .venv-cpu/bin/python -m nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=-1 esmfold2-featured/test-01.ipynb

Use .venv-model for the Codex/Opus inference notebooks and select an available GPU through CUDA_VISIBLE_DEVICES. Their cells acquire any additional axis-specific third-party tools. The pinned CUDA12.4 PyTorch wheel requires a compatible NVIDIA driver. Do not install both requirement files into the same environment.

Optional storage settings, set before opening the kernel:
- ESMFOLD_CHECKPOINT: directory containing the converted model checkpoint. Without it, model notebooks acquire and convert the specified public weights.
- ESMFOLD_CHARGE_ROOT, ESMFOLD_CODEX_R2_ROOT, ESMFOLD_OPUS_R2_ROOT: shared calculation directories for those investigations. Defaults are shown in each notebook.
- ESMFOLD_CODEX_PREDICTION_CACHE: shared prediction cache for the Codex r2 analyses. Every reused prediction must pass its sequence/model/settings and coordinate-hash checks.

A successful validation JSON records the executed notebook hash, cell count, host and calculation-receipt locations. A notebook without a completed validation receipt is not a verified full execution. FAMILY_VALIDATION.json indexes the saved local completion state and excludes the unperformed membrane candidate from the scientific-completion count.

The membrane-topology entry documents an unperformed candidate. It contains no invented outcome curve or independent negative result.
