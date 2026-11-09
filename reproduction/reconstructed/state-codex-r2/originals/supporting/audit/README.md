# Audit workspace

Status: complete. A low-dose STATE generalizability failure was certified on
the frozen ST-HVG-Tahoe zero-shot test; A1 distance remained negative. See
`report/REPORT.md`.

All audit-owned artifacts live here. `data/target_locked/.locked` is the access
sentinel. Run `python audit/scripts/controller.py status` to inspect the gate.

The `external/` directory contains pinned upstream repositories and is recorded
in the provenance manifest; no stored SPECTRA run, finding, provenance,
download, or artifact is used.

The original Tahoe magnitude transport remains a documented resource gap. The
separate dose rescue used official released scores and a frozen same-example
reference. Nothing was submitted to a SPECTRA pending queue.
