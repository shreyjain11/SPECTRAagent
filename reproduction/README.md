# Executable analysis notebooks

Start with the [inline notebook guide](inline/README.md) and [notebook index](inline/INDEX.md). The registry covers 143 entries across 28 investigations. Each preferred notebook has six sections: data acquisition, processing, axis and levels, model results or released scores, curves and controls, and the calculated decision with its explanation. Custom calculation code executes directly in the visible cells.

The index and [execution review](PR_REVIEW.md) distinguish completed executions, documented unperformed candidates, and entries still awaiting execution. Completed notebooks link their rendered results and hash-bound execution evidence. Their section 6 decisions follow the displayed calculations; supporting registry summaries are not presented as newly calculated results.

Use the [environment guide](inline/README.md#setup), then run a selected analysis from the repository root:

```sh
python reproduction/run_notebooks.py --analysis state-codex-r1/test-01 --python /path/to/environment/bin/python
```

The default route requires the preferred inline notebook. It refuses pending entries instead of substituting a different implementation. Run All processes raw inputs, constructs axes and levels, and calculates results; public individual model scores are used where explicitly identified. Fine-tuning, new inference, verified prediction reuse, and comparator training are disclosed in each notebook. Large data and model files are acquired by the visible cells rather than stored in Git.

[Registry records](index.json), public input inventories and supporting materials remain available. Select `--implementation supporting` or `--implementation public-bundle` only when that alternate route is intended. The public-bundle inputs are listed in [data.json](data.json) and prepared with `python reproduction/prepare_inputs.py --all`.

Validate all registry links, included payloads, and preferred notebook evidence with:

```sh
python reproduction/validate.py
```

`integrate_inline.py --source /path/to/review-directory` refreshes the preferred route from completed, hash-matching notebook executions. It does not execute analyses or infer success from notebook existence. The website, hosted API, and scientific manuscript are separate from this notebook route.
