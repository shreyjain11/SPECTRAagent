# Original AlphaMissense primary analyses

Seven notebooks preserve the original clinical screens and73-assay DMS panel,
including rejected depth/support candidates, accepted occupancy evidence and
controls. Evaluation joins **released AlphaMissense predictions** to the exact
clinical/DMS records. Fresh neural inference was not part of the original method.

Use Python3.11 from this directory:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python am_inputs.py --profile axis-4 --offline
.venv/bin/python ../execute_notebook.py am-primary/axis-4.ipynb --cwd am-primary
```

Then open `am-primary/axis-4.ipynb` with this environment as its kernel. Each
notebook's first cell restores only its input profile. `.py` exports preserve
code-cell order. The full original frozen cohort metadata, released-score subset,
DMS members and comparison targets are verified by SHA256. New calculations go
to ignored `am-primary/recomputed/` and `upstream_checks/reconstructed/` folders.

Axis1 additionally needs the original complete UniRef search output, a single
183MB gzip file. Its exact hash and versioned public GitHub release URL are in
`payload_manifest.json`; bootstrap downloads it only when absent. Axis2 and the
five DMS analyses do not need that file. To prepare everything:

```sh
.venv/bin/python am_inputs.py --profile all
```

Publication status of that external asset is explicit in the manifest and must
be `verified_public` before downloading. `--asset-dir` is an optional local cache
of the same named, hash-checked release assets; it never permits alternative data.

The source-reconstruction section remains executable. `RUN_DOWNLOADS=True`
fetches the exact dated ClinVar2026-06-06, released AlphaMissense scores, gnomAD or
ProteinGym v1.3 sources and stages outputs through the original preparation/join
functions. Clinical preparation requires `bcftools`. `DOWNLOAD_FULL_MSAS=True`
verifies all66 selected public MSA members. On Linux x86-64,
`REBUILD_ALIGNMENTS=True` uses the original MMseqs executable/parameters. The
optional `REBUILD_UNIREF_SEARCH` route pins the original UniRef2026_01 database,
whose full download is268GB. These expensive options stay off by default.

The portable default uses hash-verified arrays from the recorded Linux alignment
reconstruction, then executes original mapping, scoring, bootstrap and curves.
It does not run clustering merely because the machine is Linux. The supplemental
reconstruction reproduced65 of66 alignments exactly;37 OTU7A positions differ in
weighted counts/depth. Original occupancy flags and levels, AlphaMissense
statistics and DMS dynamic-range results match; only small PSSM summary values
change. The notebook keeps that comparison separate from the original frozen
feature track and preserves the agent's historical decision.

`payload_manifest.json` describes bounded semantic Git packs and the external
search asset. The duplicate563MB MSA archive and generated94MB cluster tables
are omitted; the public member-verified recipe replaces their acquisition role.
`acquisition/download_sources.json` contains URLs, versions and hashes.
`traceability.json` links all seven original analyses to their complete chains.
`PORTABLE_VALIDATION.json` separates packaged-copy validation from historical
outputs and from expensive raw-source operations not rerun during integration.
