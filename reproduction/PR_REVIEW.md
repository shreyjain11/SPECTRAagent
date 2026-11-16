# Notebook execution review

The catalog covers 143 entries across 28 investigations. Open the [notebook index](inline/INDEX.md) or [setup guide](inline/README.md) to review and run the notebooks.

Original execution receipts cover **142 analysis notebooks on exxact05**; one entry documents an unperformed candidate. Subsequent [scientific corrections](corrections/scientific_20261115/README.md) reran 10 full STATE notebooks and the affected calculation cells in 11 other notebooks on the recorded local host. Their current receipts distinguish these scopes and preserve the earlier executions. Execution completion does not establish the scientific conclusion or external confirmation.

| Model | Executed analyses | Unperformed candidates | Pending | Total |
|---|---:|---:|---:|---:|
| AlphaMissense | 34 | 0 | 0 | 34 |
| ESMFold2 | 34 | 1 | 0 | 35 |
| STATE | 44 | 0 | 0 | 44 |
| CONCH | 30 | 0 | 0 | 30 |

## Review criteria

Each preferred notebook places its custom calculation code in six numbered sections:

1. Data source and acquisition.
2. Data processing.
3. Axis definition and level construction.
4. Model results or released scores.
5. Curves and controls.
6. Calculated decision and explanation.

Completed entries have executed cells, no error outputs, rendered results, and execution evidence matching the published notebook and HTML hashes. Input and eligibility screens explain where evaluation stopped. The unperformed membrane candidate has no model-performance claim.

STATE and AlphaMissense notebooks identify the public individual scores they use. ESMFold2 and CONCH notebooks identify whether their results use released measurements or fresh inference. Model prediction caches are checked against the inputs and settings specified in the cells. Custom scientific calculations are visible inline.

The registry and runner select the verified inline notebook by default. Section 6 supplies its calculated result. Pending entries cannot silently select a supporting implementation.

## Validation

`python reproduction/test_scientific_revision.py` checks the scientific-correction receipt schema, including preservation of unexecuted cells and the original evidence chain. Numerical comparisons and independently checked uncertainty calculations are linked from the correction report.


Run `python reproduction/validate.py` from the repository root to check all 143 registry entries, preferred notebook hashes and section maps, included input manifests, and supporting artifact links. [Packaging checks](inline/PACKAGING_VALIDATION.json) also record the runner test on exxact05.
