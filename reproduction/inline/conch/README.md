# CONCH notebooks

Each notebook contains six sections: input acquisition, processing, axis and level construction, model results or eligibility checks, curves and controls, and the decision. The analysis-specific code is inline. Model code comes from the pinned public CONCH library and the explicitly named public reference models.

Use Python 3.11 and two separate environments. The six `conch-primary` notebooks use newer numerical-library versions; all Opus, GPT and Kimi notebooks use the shared environment. Do not install both requirement sets into the same environment.

| Notebook folders | Requirements | Kernel |
| --- | --- | --- |
| `conch-primary` | `requirements-primary.txt` | `conch-primary` |
| `conch-opus-r1`, `conch-opus-r2`, `conch-gpt-r1`, `conch-gpt-r2`, `conch-kimi-r1`, `conch-kimi-r2` | `requirements-shared.txt` | `conch-shared` |

From this directory, install the environment needed for a notebook:

```bash
python3.11 -m venv .venv-conch-primary
.venv-conch-primary/bin/python -m pip install torch==2.5.0 torchvision==0.20.0 --index-url https://download.pytorch.org/whl/cu124
.venv-conch-primary/bin/python -m pip install -r requirements-primary.txt
.venv-conch-primary/bin/python -m ipykernel install --user --name conch-primary --display-name "CONCH primary"
```

```bash
python3.11 -m venv .venv-conch-shared
.venv-conch-shared/bin/python -m pip install torch==2.5.0 torchvision==0.20.0 --index-url https://download.pytorch.org/whl/cu124
.venv-conch-shared/bin/python -m pip install -r requirements-shared.txt
.venv-conch-shared/bin/python -m ipykernel install --user --name conch-shared --display-name "CONCH shared"
```

Select the matching kernel before Run All. The CUDA 12.4 wheels require a compatible NVIDIA driver. The notebooks select CPU when CUDA is unavailable; the verified full executions used exxact05. The setup files pin the direct scientific and notebook dependencies. The notebook notes also give standalone commands when copying one notebook by itself.

Authenticate with Hugging Face using an account that can download `MahmoodLab/conch`, for example with the environment's `huggingface-cli login`. The notebook verifies the checkpoint SHA-256 and uses public CONCH commit `141cc09c7d4ff33d8eda562bd75169b457f71a62`.

For GPT/Kimi notebooks, the default raw-input directory is `inputs/` under the notebook working directory. Set `CONCH_INPUTS` before launching the kernel to reuse an existing shared input directory. Primary/Opus notebooks show their corresponding input-directory settings in section 1. Keep the raw input caches between notebooks: the NCT normalized and non-normalized parquet datasets together occupy about 27 GB, in addition to image exports and model weights. Downloaded files are checked by the inline acquisition code.

The model transform is part of each notebook's protocol. GPT R1, GPT R2 and Kimi R1 explicitly use CONCH 224×224 inputs. Primary, Opus and Kimi R2 use the public CONCH default 448×448 input transform. Image perturbations and pixel measurements occur at the resolutions specified in each notebook; these settings should not be conflated.

Kimi R2 additionally uses OpenCLIP 2.24.0 (`ViT-B-32`, `laion2b_s34b_b79k`) and public DINOv2 `dinov2_vitb14` at commit `7764ea0f912e53c92e82eb78a2a1631e92725fc8`. Their weights are acquired by the inline model cells. DINOv2 inference uses standard PyTorch attention; `xformers` and the DINO training packages are not required. Other reference models and weight identities are specified in their scoring cells.

`VALIDATION.json` lists each notebook's local execution verification, section count, embedded figures and file hashes. GPT/Kimi per-notebook execution receipts distinguish the executed artifact hashes from subsequent Markdown-only setup additions and confirm that executed code and outputs did not change. HTML files preserve the figures and results for review without execution. Eligibility-only candidates show their diagnostic and decision without claiming an unmeasured model-performance curve.
