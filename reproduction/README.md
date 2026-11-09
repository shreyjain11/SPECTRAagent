# Original investigation workflows and analysis records

Start with the [44 primary notebooks](primary/README.md). They link the original data sources and processing, axis definitions, level construction, model results or released scores, curves or screening diagnostics, and the historical agent decisions. Retained, discarded and unresolved candidates remain represented.

The [index](index.json) lists all 28 investigations and 143 entries. The [whole-PR review](PR_REVIEW.md) distinguishes 44 recovered primary workflows, 32 additional calculation replays with downloadable inputs, and 67 evidence/summary displays whose original individual calculations remain missing. All retained notebooks have input preparation routes; successful execution of a summary display does not restore the missing original work.

## What the records contain

Each analysis retains `dataset_split`, `axis_levels`, `model_evaluation`, `curve` and `insight`. For the recovered primary entries, `implementation` points to the current rich notebook and Python export, and `primary_recovery.stages` explicitly connects all seven stages. Its paths resolve relative to the named package. The public-bundle code-only export and its notes are preserved under `legacy_*`. Its preparation route remains available alongside the preferred primary notebook.

`historical_decision` links an attributed record in [historical_decisions.json](historical_decisions.json). These summaries preserve the original recorded disposition and result, not a new reviewer judgment. Primary notebooks additionally link recovered ledgers, reports or original decision excerpts. A candidate discarded before scoring has its original diagnostic, not an invented performance curve.

`traceability_review.json` reviews every entry against this workflow criterion. It does not demand new confirmation studies, repairs to historical scientific conclusions, or fresh model inference that the original agent never performed. Older `reconstruction_notes` can contain scientific context as well as missing inputs; the workflow review does not treat every such note as a reproduction requirement.

## Inputs and execution

The primary packages carry small, checksum-verified compressed input packs, original code and portable bootstrap helpers. Large raw datasets and model weights use the pinned public acquisition recipes. The original AlphaMissense UniRef50 search-hit table exceeds GitHub's Git-file limit and is a versioned, checksum-verified release asset linked by its package manifest. No private cloud bucket or access to the original analysis server is required.

Default primary execution replays retained historical measurements. ESMFold2 and CONCH have an explicit full-workflow switch connecting acquisition, processing, model scoring and their original analyses. Missing generated results stop those runs; they cannot silently substitute archived predictions. Full raw-data/model execution has not been performed during this integration. CONCH's model download requires the original publisher's access approval.

STATE starts from the official per-record evaluation files the original agent used. AlphaMissense starts from released prediction scores. Neither original workflow requires a new target-model inference run. The current ESMFold2 implementation is a documented replacement for the older historical fork; prediction equality across implementations is not claimed.

The `materials/`, `inputs/`, `samples/` and `code/` inventories remain for the additional investigations and public-bundle exports. Four checksum-verified archives are listed in [data.json](data.json) and the [public input release](https://github.com/shreyjain11/SPECTRAagent/releases/tag/notebook-inputs-2026-11-08-v1). These supply retained features, measurements, predictions, structures or images, not merely sample identifiers. The full download is about 3.3 GB; `SPECTRA_DATA_DIR` selects its cache location.

```sh
python reproduction/prepare_inputs.py --all
python reproduction/run_notebooks.py --all --implementation public-bundle --workers 4
```

Install `reproduction/requirements.txt` for that public-bundle route. `execution.json` records its original execution checks and binds each result to the corresponding `materials/` notebook hash. The preferred primary notebooks instead use their model-specific environments and package checks; see [primary setup](primary/README.md). The bulk runner defaults to preferred notebooks, and `--primary-only` restricts it to those 44. Use `--python` or its per-model interpreter options to select the environments. Outputs are written under `reproduction/.executions/` or the location selected by `--output`.

## Checks

```sh
python reproduction/validate.py
```

This checks all 143 records, preferred and public-bundle notebook hashes, archive mappings, seven-stage primary links, attributed historical decisions, sample tables and bundled payload hashes. Model-specific package validation records distinguish actual clean-package replay checks from optional full runs. `integrate_primary.py` refreshes the primary links and review after an intentional package change.

The website, hosted API and scientific protocol are unchanged. This PR neither merges its own changes nor imports findings into a hosted service.
