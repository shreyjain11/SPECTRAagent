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
- Each investigation has a plain-language summary. Each test explains the measured property and the comparison before presenting the result. “Measurements, data and code” opens a notebook for that test. The browser displays its code, narrative and saved outputs. To rerun a notebook that links to a full model bundle, download and extract that bundle and follow its README; the `.ipynb` download alone does not include its external inputs and code. Older notebooks may embed their retained inputs. Unmeasured tests identify what was unavailable. HTML, JSON and Markdown views use the same records. Audit dates refer to the audit record.
- The supplied bundle includes one nbformat 4 document per test at `public/registry/notebooks/<audit-id>/test-NN.ipynb`. Notebook metadata identifies the audit, test, and output type. The viewer reads these files at build time.
- Output types are `curve`, `comparison`, `table`, `none`, and `analysis`. The `analysis` type accommodates a shared workflow with mixed outputs; a related chart in that workflow does not establish a separate curve for every test that links to it.
- Current notebooks describe coverage in `metadata.spectra.reproducibility`: five ordered stages (`dataset`, `axis`, `evaluation`, `curve`, `insight`), each with an `id`, `label`, `status` and `detail`; a `missing` array describing limits and missing inputs; and an `end_to_end` boolean. Status text describes the retained evidence and is not a scientific acceptance decision. An `end_to_end` value of `true` requires an empty `missing` array. A value of `false` may reflect retained study-design limits even when all five stages can be replayed. Optional `metadata.spectra.bundleUrl` links to a site-relative path or HTTPS download. Per-model ZIPs belong at `public/registry/reproduction/<model>.zip` and contain the notebooks, retained inputs, code and run instructions. These private source collections and their generated downloads remain outside Git.
- `/registry/audits.json` contains the full collection. A record's `legacyFindingId`, when present, identifies the corresponding earlier hosted finding. Records without a match are separate investigations.
- An optional axis `review_note` records a reproduction finding alongside the historical result and decision. It appears immediately below the result in investigation and notebook pages, and is preserved in Markdown and JSON exports.
- The source bundle retains its original figure manifest for provenance. The pages and Markdown downloads display no figure panels or figure links. `/registry/evidence-manifest.json` lists evidence files and checksums.
- `npm run check:registry` checks row and record identity, figure and evidence checksums, plain-language explanations, shared navigation, per-axis content in rendered pages, and links to local evidence. It validates coverage metadata when present and checks local full-bundle downloads. Run `SPECTRA_REQUIRE_REPRODUCIBILITY=1 npm run check:registry` to require coverage metadata for every notebook. The default also supports older collections without coverage metadata.

Passing these checks confirms the renderer's contract and the recorded execution state. It does not rerun the scientific analyses, establish fresh model inference, supply missing evidence or certify the scientific conclusions. A stage can remain unavailable even when every supplied code cell executes successfully.

Install the reviewed registry pages and their referenced assets together. The existing hosted API, moderation queue, findings export, and registry entries for other models retain their existing URLs. If a maintainer also imports the collection into the hosted database, match the explicit legacy identifiers, preserve unrelated records and run the service's review process. This repository supplies the website renderer. The hosted backend owns database imports and publication.
