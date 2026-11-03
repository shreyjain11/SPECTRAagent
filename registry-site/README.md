# Manuscript registry

The registry follows the four primary investigations and the 24 additional audits in Figures 2–5. Each investigation has a stable URL, a model, an audit date or documented date range, an audit host, and its evaluated axes. A decision belongs to an axis. A control, an unresolved test, and an audit of a different model have distinct meanings.

## Build a review copy

The source data and evidence live outside Git. Extract the maintainer-supplied manuscript collection to a folder containing `investigations.json` and `public/registry/`. Set `SPECTRA_REGISTRY_BUNDLE` to the absolute path to that folder.

```sh
npm ci
npm run check
npm run check:registry
```

The standard site is written to `dist/`. The separate registry build is written to `.registry-build/`. To review both locally, copy the two build directories into the same empty preview directory and serve it over HTTP. The registry opens at `/registry/`.

## Contents and checks

- `/registry/` lists the four models. Each model page links to the exact main and supplementary figure PDFs and seven investigations in figure order.
- Each investigation has HTML, JSON and Markdown views. JSON retains the axis definition, evidence, result, and links to available code and data. Figure numbering follows the manuscript. Audit dates refer to the audit record.
- `/registry/audits.json` contains the full collection. A record's `legacyFindingId`, when present, identifies the corresponding earlier hosted finding. Records without a match are separate investigations.
- `/registry/figures/sources.json` records the original Overleaf filenames and SHA-256 checksums. `/registry/evidence-manifest.json` lists evidence files and checksums.
- `npm run check:registry` checks row and record identity, figure and evidence checksums, per-axis content in rendered pages, and links to local evidence.

Install the reviewed registry pages and their referenced assets together. The existing hosted API, moderation queue, findings export, and registry entries for other models retain their existing URLs. If a maintainer also imports the collection into the hosted database, match the explicit legacy identifiers, preserve unrelated records and run the service's review process. This repository supplies the website renderer. The hosted backend owns database imports and publication.
