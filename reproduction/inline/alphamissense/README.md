# AlphaMissense analyses

Each notebook contains its acquisition, processing, axis construction, score joins, statistics, figures, and interpretation in six sections. Run All executes these calculations; it does not read an aggregate result table as its answer. The adjacent HTML files show the completed outputs when a matching validation record reports `completed: true`.

Use Python 3.11 with `requirements.txt`. The primary alignment-weighting notebooks require Linux x86-64; their acquisition cells download and verify the specified MMseqs2 binary. The Opus notebooks additionally require their stated protein-search dependency. AlphaMissense predictions are released substitution scores: these analyses do not train or fine-tune the model.

Set `AM_RAW_INPUTS` to a shared raw-input directory before starting a kernel to reuse downloaded files. Every fixed input is checked against its displayed fingerprint. Inputs collected from a versioned web service receive a source receipt with their exact identifier, response fingerprint, and retrieval status. `AM_ARCHIVE_CACHE` can point to a directory containing the public input archive. `AM_MMSEQS_THREADS` controls MMseqs2 threads and defaults to 8. Calculated outputs are written to `calculated_outputs` below the notebook's working directory; use a separate working directory for each simultaneous notebook.

The first run can require substantial downloads, especially the whole-genome conservation track and reference genome. Raw files are reused after verification; the scientific calculations are repeated. Source versions, cohort exclusions, residue-numbering maps, and unavailable annotations are shown explicitly in each notebook. A screening notebook can close an axis before target-performance analysis when the necessary annotation or study design is unavailable; it reports the actual eligibility diagnostics without inventing performance results.

Validation records include the execution host, executed and total cell counts, errors, notebook fingerprint, HTML fingerprint, and output receipt. A prepared notebook without a completed matching record is not a verified result.
