# SPECTRAagent

The public website and scientific protocol for **AutoSPECTRA**: a workflow for
investigating how model performance changes as evaluation data become less
similar to training data.

[Visit AutoSPECTRA](https://spectra.yashaektefaie.com/) ·
[Read the protocol](protocol/protocol.md) ·
[Contribute](CONTRIBUTING.md)

The website helps researchers start an audit with their coding agent, find
prior findings, and submit completed work for review. The agent executes the
investigation using the researcher's tools, data, model access, and compute.

This repository contains the static Astro site and versioned protocol sources.
The findings registry and submission service are hosted separately. Development
history and research implementation remain in the separate `SPECTRAagent-dev`
repository.

## Local development

Use Node.js 22 or later:

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
| `protocol/CHANGELOG.md` | Protocol changes and version history |
| `public/` | Static assets and generated protocol copies |
| `scripts/sync-protocol.mjs` | Copies protocol sources to their public URLs |
| `scripts/check-site.mjs` | Verifies required content in the built site |
| `.github/workflows/check.yml` | Pull-request and branch checks |

Protocol changes are welcome through pull requests. Describe the scientific
reason for a change, the behavior it affects, and any implications for earlier
audits. See [CONTRIBUTING.md](CONTRIBUTING.md) for review and versioning.

## Hosted services and deployment

The live findings index at
[/data/findings.json](https://spectra.yashaektefaie.com/data/findings.json) belongs
to the existing registry service. Its data and backend are outside this
repository. A local site build does not create a registry or reproduce the
hosted submission service.

No automatic deployment is configured here. After reviewing a passing build, a
maintainer deploys `dist/` through the existing hosting setup. The release must
preserve the hosted `/data/findings.json` route and other service routes; a
static-site release must not replace the registry with an empty local copy.
Verify the homepage and the `/protocol.md`, `/finish.md`, and `/agents.md`
endpoints after deployment, along with access to the existing findings index.

## License

See [LICENSE](LICENSE).
