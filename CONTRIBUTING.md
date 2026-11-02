# Contributing

Contributions to the AutoSPECTRA website, scientific protocol, prompts, and
documentation are welcome. You do not need to write code to contribute:
[open an issue](https://github.com/yashaektefaie/SPECTRAagent/issues/new) to ask a
question, suggest an improvement, report a bug or broken link, or discuss a
scientific change. Include what happened, what you expected, and enough detail
to reproduce a problem. Hosted-service problems can also be reported here,
even though the backend is maintained separately. Keep credentials, receipt
tokens, and private research data out of public reports.

To contribute a completed audit, use the [submission guide](protocol/submit.md).
Use pull requests for changes to the website and instructions.

## Make and check a change

1. [Fork the repository](https://github.com/yashaektefaie/SPECTRAagent/fork) into
   your account and clone your fork locally.
2. Create a branch for your change and edit the appropriate source files below.
3. Run the checks and inspect the affected content or website interactions.
4. Commit your changes and push the branch to your fork.
5. [Open a pull request](https://github.com/yashaektefaie/SPECTRAagent/compare)
   from your fork's branch to `yashaektefaie/SPECTRAagent`, with `main` as the
   base branch. Fill in the pull-request template and respond to review feedback.

For a small wording correction, GitHub's file editor can create a fork and pull
request directly in the browser. You can also describe a suggested correction
in an issue if you are unsure how to edit it.

For local development, use Node.js 22.12 or later:

```sh
npm ci
npm run dev
```

Website source lives in `src/`. Edit protocol documents in `protocol/`:

- `protocol.md` defines the scientific investigation workflow.
- `finish.md` defines the review and completion gates.
- `agents.md` explains the hosted HTTPS run/find/submit routes.
- `prompt.md` contains the starting prompt and compute/access placeholders.
- `submit.md` explains schema validation, submission, and receipt-status checks.

The development and build prehooks copy these documents to `public/`. Change
the canonical sources rather than editing generated copies. Keep website
prompts, linked document paths, and the protocol consistent.

Before submitting:

```sh
npm run check
npm run preview
```

`npm run check` builds the site and checks the generated output. After editing
protocol sources during a development session, run `npm run sync:protocol` or
restart the development server. Rebuild before inspecting a changed production
preview.

For website changes, inspect the result at narrow and wide viewport widths,
check keyboard navigation and links, and exercise the prompt-selection and
copy controls. Include screenshots when they help reviewers assess a visual
change.

Keep prompts and guides consistent with the hosted service contract. Discovery
starts at `/api/models` and follows returned model, axis, and card links; agents
read relevant cards in both JSON and Markdown. Submission uses the current
`/api/submissions/schema`, validation at `/api/submissions/validate`, and a JSON
`POST` to `/api/submissions`. The body is the full schema bundle, not just a
finding or a report path. Status checks use the returned receipt token in an
authorization header. Preserve the distinction between validation, queued
review, acceptance, and confirmed publication. Never put real receipt tokens
or credentials in examples, screenshots, or committed files.

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
Update both protocol and finish-review versions when a change affects both;
their version numbers need not match for a change that affects only one.
Record the rationale and compatibility implications in the changelog. Pure
formatting or typo corrections can be documented without changing the
scientific version.

## Scope and release

Keep this repository focused on the website and protocol. Research run files,
model checkpoints, private data, and registry records belong outside it. The
hosted API, artifacts, findings export, and submission queue are maintained
separately. Reference their public contracts without adding backend code,
local result data, or copied registry records. User intent determines whether
an agent runs, finds, or submits an audit; reading a guide is not authorization
to perform all three. New submissions must remain separate records, including
when another audit already covers the same model and axis.

Pull requests run checks but do not automatically deploy. A maintainer reviews
the change and publishes the built `dist/` through the existing hosting setup,
preserving `/api/*`, `/downloads/*`, and `/data/findings.json` and their existing
data. A static-site release does not update the hosted backend or publish audit
results. Do not configure an automatic deployment as an incidental part of a
website or documentation change.

For a release, record the reviewed source revision and protocol versions,
retain a recoverable copy of the previous static release, and verify the
homepage, assets, five instruction documents, and hosted discovery links.
Confirm the submission schema and existing artifact/download routes remain
available. Use validation for contract checks; do not create test submissions
in the public queue as a release smoke test. If a static release fails, restore
the previous static files while leaving registry records and the submission
queue intact. Follow the checks in the
[README](README.md#hosted-services-and-deployment).
