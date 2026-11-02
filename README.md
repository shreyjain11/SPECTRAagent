# SPECTRAagent

The public website and scientific protocol for **AutoSPECTRA**: a workflow for
investigating how model performance varies across measurable properties of
inputs and evaluation conditions. An audit proposes and tests axes such as
training support, sequence composition, or image resolution, then examines
whether the evidence supports the resulting interpretation.

[Visit AutoSPECTRA](https://spectra.yashaektefaie.com/) ·
[Read the protocol](protocol/protocol.md) ·
[Contribute](CONTRIBUTING.md)

The website helps researchers start an audit with their coding agent, find
prior findings, and submit completed work for review. The agent executes the
investigation using the researcher's tools, data, model access, and compute.

This repository contains the static Astro site and versioned protocol sources.
The registry, submission service, audit records, and supporting datasets remain
hosted separately. A local website build does not run an audit or start a backend.

## Run, find, or submit an audit

Give your coding agent the [agent guide](https://spectra.yashaektefaie.com/agents.md),
or use a prompt on the [website](https://spectra.yashaektefaie.com/).

- **Run:** use the [starting prompt](protocol/prompt.md), filling in the model
  and available compute/access. The agent follows the
  [protocol](protocol/protocol.md) and [finish review](protocol/finish.md),
  using the researcher's tools and resources.
- **Find:** start at the hosted [model index](https://spectra.yashaektefaie.com/api/models)
  and follow its model, axis, and audit-card links. Read all relevant cards in
  JSON and Markdown, including their evidence, limitations, and source links.
  Several audits may examine the same model and axis.
- **Submit:** follow the [submission guide](protocol/submit.md). Fetch the
  current schema with `GET /api/submissions/schema`, validate the full JSON
  bundle with `POST /api/submissions/validate`, then submit it with
  `POST /api/submissions`. These routes are on the hosted AutoSPECTRA domain.
  Both new and existing models are supported; a new audit does not overwrite
  an existing one.

Submission returns an ID, status, receipt token, and status URL. Save the token
privately and check `GET /api/submissions/{id}` using
`Authorization: Bearer <receipt_token>`. `pending_review` means queued for
review, not accepted or published. A successful validation checks the contract;
it is not a scientific review or publication decision. The hosted schema and
guides define the current access requirements and request details.

Reading the guide alone does not authorize running an audit or submitting
results. Agents need HTTPS reading capability for discovery and JSON `POST`
capability for submission; no connector setup is required. Large supporting
artifacts are referenced by stable URLs and checksums, not uploaded as local
paths or embedded in the submission body.

## Local development

Use Node.js 22.12 or later:

```sh
npm ci
npm run dev
```

Open the local address printed by Astro. To build and inspect the production
site:

```sh
npm run build
npm run preview
```

Run the repository checks before opening a pull request:

```sh
npm run check
```

The development and build commands copy canonical protocol files into the
public directory automatically. Edit the files in `protocol/`; generated copies
in `public/` are build inputs, not separate sources to maintain.
After editing a protocol file while `npm run dev` is running, run
`npm run sync:protocol` or restart the development server to refresh its copy.
For `npm run preview`, rebuild with `npm run build` to update `dist/`.

## Repository structure

| Path | Purpose |
| --- | --- |
| `src/` | Astro pages, components, and styles |
| `protocol/protocol.md` | Scientific audit procedure |
| `protocol/finish.md` | Review and completion criteria |
| `protocol/agents.md` | Agent guide for running, finding, and submitting audits |
| `protocol/prompt.md` | Starting prompt with model and compute/access placeholders |
| `protocol/submit.md` | HTTPS submission and receipt-status workflow |
| `protocol/CHANGELOG.md` | Protocol changes and version history |
| `public/` | Static assets and generated protocol copies |
| `scripts/sync-protocol.mjs` | Copies protocol sources to their public URLs |
| `scripts/check-site.mjs` | Verifies required content in the built site |
| `.github/workflows/check.yml` | Pull-request and branch checks |

Protocol changes are welcome through pull requests. Describe the scientific
reason for a change, the behavior it affects, and any implications for earlier
audits. See [CONTRIBUTING.md](CONTRIBUTING.md) for review and versioning.

## Hosted services and deployment

The hosted `/api/*` routes serve model/axis/card discovery and submissions.
Curated artifacts are available at `/downloads/*`, and the existing
[/data/findings.json](https://spectra.yashaektefaie.com/data/findings.json) export
remains available. The backend and these data are outside this repository.
Local development uses the hosted service links; it does not create local API
routes or a registry.

No automatic deployment is configured here. After reviewing a passing build, a
maintainer deploys `dist/` through the existing hosting setup. Preserve the
hosted `/api/*`, `/downloads/*`, and `/data/findings.json` routes and their data.
Do not replace the hosting root or registry data with the static build.

After deployment, verify the homepage, its assets and prompt controls, and the
`/protocol.md`, `/finish.md`, `/agents.md`, `/prompt.md`, and `/submit.md`
documents. Follow a model-to-axis-to-card path through the API, open the card's
JSON and Markdown links, and check a supporting download, the submission
schema, and the existing findings export. Release checks must not create
unrequested public submissions. See [CONTRIBUTING.md](CONTRIBUTING.md) for
review and release responsibilities.

## License

See [LICENSE](LICENSE).
