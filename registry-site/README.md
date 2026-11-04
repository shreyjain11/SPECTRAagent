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

- `/registry/` describes the four models and links to seven investigations per model. Pages use the homepage’s shared header, logo, fonts and footer.
- Each investigation has a plain-language summary. Each test explains the measured property and the comparison before presenting the result. Measurements, data and code are available in expandable sections. HTML, JSON and Markdown views use the same records. Audit dates refer to the audit record.
- `/registry/audits.json` contains the full collection. A record's `legacyFindingId`, when present, identifies the corresponding earlier hosted finding. Records without a match are separate investigations.
- The source bundle retains its original figure manifest for provenance. The pages and Markdown downloads display no figure panels or figure links. `/registry/evidence-manifest.json` lists evidence files and checksums.
- `npm run check:registry` checks row and record identity, figure and evidence checksums, plain-language explanations, shared navigation, per-axis content in rendered pages, and links to local evidence.

Install the reviewed registry pages and their referenced assets together. The existing hosted API, moderation queue, findings export, and registry entries for other models retain their existing URLs. If a maintainer also imports the collection into the hosted database, match the explicit legacy identifiers, preserve unrelated records and run the service's review process. This repository supplies the website renderer. The hosted backend owns database imports and publication.
