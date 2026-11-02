# Contributing

Contributions to the AutoSPECTRA website and scientific protocol are welcome.
Open an issue to discuss a proposed scientific change, or submit a focused pull
request with the rationale and evidence needed to review it.

## Make and check a change

Use Node.js 22 or later, then work from a branch:

```sh
npm ci
npm run dev
```

Website source lives in `src/`. Edit protocol documents in `protocol/`:

- `protocol.md` defines the scientific investigation workflow.
- `finish.md` defines the review and completion gates.
- `agents.md` explains how agents use the website and hosted services.

The development and build prehooks copy these documents to `public/`. Change
the canonical sources rather than editing generated copies. Keep website
prompts, linked document paths, and the protocol consistent.

Before submitting:

```sh
npm run check
npm run build
npm run preview
```

For website changes, inspect the result at narrow and wide viewport widths,
check keyboard navigation and links, and exercise the prompt-selection and
copy controls. Include screenshots when they help reviewers assess a visual
change.

## Review scientific changes explicitly

In the pull request, explain:

- The problem and the proposed change to agent or researcher behavior.
- The scientific rationale, supporting evidence, and relevant limitations.
- Whether the change affects axis selection, leakage controls, replication,
  evidence interpretation, resource limits, or completion criteria.
- Whether earlier audits remain comparable and how their recorded protocol
  versions should be interpreted.

Preserve distinctions between exploratory and confirmed evidence, panel
adequacy and scientific rejection, and predictive association and causal
explanation. Do not turn an editorial change into an unstated change in the
acceptance criteria. Substantive protocol changes require maintainer review;
a passing website check cannot validate a scientific rule.

For a change to scientific behavior, update the `Version:` field in the affected
protocol documents and add an entry to `protocol/CHANGELOG.md`. Use the existing
`YYYY-MM-DD.N` convention, increasing `N` for another revision on the same date.
Keep protocol and finish-review versions aligned when a change affects both.
Record the rationale and compatibility implications in the changelog. Pure
formatting or typo corrections can be documented without changing the
scientific version.

## Scope and release

Keep this repository focused on the website and protocol. Research run files,
model checkpoints, private data, and registry records belong outside it. The
live `/data/findings.json` route and submission service are maintained
separately; reference their public contracts without adding local result data.

Pull requests run checks but do not automatically deploy. A maintainer reviews
the change and publishes the built `dist/` through the existing hosting setup,
preserving the registry and service routes. Follow the release checks in the
[README](README.md#hosted-services-and-deployment).
