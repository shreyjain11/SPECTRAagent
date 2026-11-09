# Primary investigation notebooks

These 44 notebooks reproduce the original primary investigations. Each links data acquisition and processing, the axis definition and level rules, original model measurements or released scores, curves or screening diagnostics, and the historical agent decision. The task is to reproduce what happened; no new scientific acceptance criteria are imposed.

Default mode replays the original retained measurements. ESMFold2 and CONCH additionally provide `RUN_ORIGINAL_WORKFLOW=True` (or the runner’s `--original-workflow`) for raw-data acquisition, processing, model scoring and the original analyses. Those full model runs have not been executed during this integration. STATE and AlphaMissense originally consumed released scores/predictions; fresh target-model inference is not required to reproduce them.

## Setup and input files

| Model | Setup and run instructions | Input handling |
| --- | --- | --- |
| ESMFold2 | [README](esmfold2/README.md), [environments](esmfold2/ENVIRONMENTS.txt) | Small offline archive restores exact original code and tables; full mode fetches pinned structures, alignments and model sources. |
| STATE | [README](state/README.md) | Exact released score files, historical annotations and expected tables are bundled in verified compressed packs. |
| CONCH | [workflow](conch/WORKFLOW.md) | Exact retained image features/logits are bundled; full mode fetches pinned images/code/checkpoint and requires CONCH access. |
| AlphaMissense | [README](alphamissense/README.md) | Small verified packs plus one versioned original UniRef50 hit-table download for the clinical homolog-count axis; public raw-input recipes are included. |

Use each model’s documented environment; their numerical package versions differ. The shared [runner](execute_notebook.py) uses the interpreter that launches it, or an explicit `--python`. It writes notebook outputs and records which run mode was requested.

The [whole-PR review](../PR_REVIEW.md) covers all 143 entries. Among the other 99 entries, 32 have executable retained calculations with public input bundles and 67 remain evidence/summary displays with missing original individual calculations. Their execution checks do not certify complete original-workflow traceability.

## ESMFold2

| Axis | Notebook | Original disposition |
| --- | --- | --- |
| Evolutionary support | [Open](esmfold2/notebooks/test-01.ipynb) | accepted |
| CAMEO difficulty, length and resolution | [Open](esmfold2/notebooks/test-02.ipynb) | control |
| Flexible / non-helical composition | [Open](esmfold2/notebooks/test-03.ipynb) | rejected |
| Absolute sequence charge | [Open](esmfold2/notebooks/test-04.ipynb) | rejected |
| Acidic windows | [Open](esmfold2/notebooks/test-05.ipynb) | rejected |
| Cysteine fraction | [Open](esmfold2/notebooks/test-06.ipynb) | accepted |
| Viral envelope proteins | [Open](esmfold2/notebooks/test-07.ipynb) | accepted |
| Potential disulfide capacity | [Open](esmfold2/notebooks/test-08.ipynb) | accepted |
| Reference geometry | [Open](esmfold2/notebooks/test-09.ipynb) | control |
| Viral-disulfide pilot | [Open](esmfold2/notebooks/test-10.ipynb) | unresolved |
| Envelope/fusion proxy | [Open](esmfold2/notebooks/test-11.ipynb) | rejected |
| Viral surface / low-helical subtype | [Open](esmfold2/notebooks/test-12.ipynb) | control |

[Per-axis evidence chain](esmfold2/traceability.json). A discarded prescoring candidate shows its original diagnostic; it does not gain an invented performance curve.

## STATE

| Axis | Notebook | Original disposition |
| --- | --- | --- |
| Chemical similarity to training drugs | [Open](state/notebooks/test-01.ipynb) | rejected |
| Dose represented in training | [Open](state/notebooks/test-02.ipynb) | rejected |
| Reactome pathway-set similarity | [Open](state/notebooks/test-03.ipynb) | accepted |
| Reactome mean | [Open](state/notebooks/test-04.ipynb) | accepted |
| Reactome log-mean (REP) | [Open](state/notebooks/test-05.ipynb) | accepted |
| Reactome minimum | [Open](state/notebooks/test-06.ipynb) | accepted |
| HGNC log-mean | [Open](state/notebooks/test-07.ipynb) | accepted |
| Gene-symbol prefix | [Open](state/notebooks/test-08.ipynb) | accepted |
| Cell context and annotation counts | [Open](state/notebooks/test-09.ipynb) | control |
| Multivariable adjustment | [Open](state/notebooks/test-10.ipynb) | control |
| Zero-shot pathway support | [Open](state/notebooks/test-11.ipynb) | control |
| Ligand-family training support | [Open](state/notebooks/test-12.ipynb) | rejected |
| Reactome cross-ontology check | [Open](state/notebooks/test-13.ipynb) | control |
| HGNC_gene_group cross-ontology check | [Open](state/notebooks/test-14.ipynb) | control |
| GO_BP cross-ontology check | [Open](state/notebooks/test-15.ipynb) | control |
| GO_MF cross-ontology check | [Open](state/notebooks/test-16.ipynb) | control |
| GO_CC cross-ontology check | [Open](state/notebooks/test-17.ipynb) | control |
| WikiPathways cross-ontology check | [Open](state/notebooks/test-18.ipynb) | control |
| KEGG cross-ontology check | [Open](state/notebooks/test-19.ipynb) | control |

[Per-axis evidence chain](state/traceability.json). A discarded prescoring candidate shows its original diagnostic; it does not gain an invented performance curve.

## CONCH

| Axis | Notebook | Original disposition |
| --- | --- | --- |
| Pooled color–texture distance | [Open](conch/notebooks/01-conch-primary.ipynb) | rejected |
| Color-only reference distance | [Open](conch/notebooks/02-conch-primary.ipynb) | unresolved |
| Texture-only reference distance | [Open](conch/notebooks/03-conch-primary.ipynb) | unresolved |
| Within-tumor tissue/stain distance | [Open](conch/notebooks/04-conch-primary.ipynb) | accepted |
| Tissue-class composition | [Open](conch/notebooks/05-conch-primary.ipynb) | control |
| Fixed reference classifiers | [Open](conch/notebooks/06-conch-primary.ipynb) | control |

[Per-axis evidence chain](conch/traceability.json). A discarded prescoring candidate shows its original diagnostic; it does not gain an invented performance curve.

## AlphaMissense

| Axis | Notebook | Original disposition |
| --- | --- | --- |
| UniRef50 homolog count | [Open](alphamissense/am-primary/axis-1.ipynb) | rejected |
| gnomAD missense-variation support | [Open](alphamissense/am-primary/axis-2.ipynb) | rejected |
| Effective alignment depth | [Open](alphamissense/am-primary/axis-3.ipynb) | rejected |
| Alignment occupancy | [Open](alphamissense/am-primary/axis-4.ipynb) | accepted |
| Occupancy at high effective depth | [Open](alphamissense/am-primary/axis-5.ipynb) | control |
| Position-specific and substitution-score references | [Open](alphamissense/am-primary/axis-6.ipynb) | control |
| Experimental dynamic range | [Open](alphamissense/am-primary/axis-7.ipynb) | control |

[Per-axis evidence chain](alphamissense/traceability.json). A discarded prescoring candidate shows its original diagnostic; it does not gain an invented performance curve.

