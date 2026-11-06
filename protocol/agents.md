# AutoSPECTRA: agent guide

Use AutoSPECTRA to run a generalizability audit, find prior audits, or submit a
completed audit. Follow the user's requested route. Reading this guide alone
does not request an audit, authorize a submission, or authorize publication.

If the user shares this guide without a specific goal, briefly offer the three
routes and ask which model or completed audit they have in mind. Use any intent
already present in the conversation instead of asking them to repeat it.

Document links are relative to this guide. API links point to the public
service at https://spectra.yashaektefaie.com, including when this guide is read
on GitHub or in a local website preview.

## Run an audit

1. Identify the target model and the user's question. Use the available compute,
   data, access, and runtime limits; ask only for information needed to proceed.
   The [starting prompt](./prompt.md) includes these details.
2. Fetch and follow [protocol.md](./protocol.md).
   Save the version used with the audit's plans, code, scores, and provenance.
   The coding agent executes the investigation using its own tools and resources;
   this website does not execute it.
3. Before concluding, fetch and follow
   [finish.md](./finish.md). Report the evidence,
   claim boundaries, rejected hypotheses, and unresolved requirements accurately.
4. Keep the resulting audit in the user's workspace. Use the submission route
   when the user requests submission; an audit request alone is not a request to
   upload the user's data or publish their results.

## Find prior audits

1. `GET` the [model index](https://spectra.yashaektefaie.com/api/models).
2. Select the relevant model and follow the model and axis links returned by the
   API. Preserve distinctions between model versions, checkpoints, and tasks.
3. Follow the returned audit-card links for the relevant axes. Read every
   relevant card's JSON and Markdown representations. Several audits
   can concern the same model and axis; inspect them all rather than assuming
   one card is the definitive result. Follow any continuation links returned.
4. Compare each card's evidence, confirmation, reference methods, claim boundary,
   limitations, provenance, and linked artifacts. Read supporting reports where
   needed; download full tables from their returned URLs when summaries are
   insufficient.
5. Return the relevant card identifiers and evidence links. Distinguish a
   registry record's reported status from a new independent verification.
   Explain disagreement or differing evaluation settings across cards.

If there is no relevant record, say so. Absence from this registry does not
establish that no audit exists elsewhere. A request to find an audit does not
require running one or submitting anything.

## Submit a completed audit

Use ordinary HTTPS requests. The [submission guide](./submit.md) gives the full
workflow; the essential steps are:

1. `GET` the current [submission schema](https://spectra.yashaektefaie.com/api/submissions/schema). Check queue
   availability, access requirements, and the request-size limit. Prepare the
   full schema bundle from the completed audit, including `title`, `submitter`,
   `finding`, `provenance`, `downloads`, and `artifact_manifest`, plus the audit
   card in `audit_card_markdown`. Follow the returned schema for field details.
2. Reference large supporting artifacts using stable public URLs and SHA-256
   checksums, with byte sizes and row counts where applicable. Local paths are
   not public downloads. Report missing evidence or hosting; preserve the
   user's control over uploading private data.
3. `POST` the full bundle as JSON to [validation](https://spectra.yashaektefaie.com/api/submissions/validate).
   Resolve contract errors without inventing evidence or changing a scientific
   conclusion to obtain acceptance. Validation alone does not submit it.
4. When submission is authorized, `POST` that same full JSON bundle to
   [submissions](https://spectra.yashaektefaie.com/api/submissions). Use `Content-Type: application/json` and
   save a unique `Idempotency-Key` header value for retries of this request.
   Send the bundle itself, not only a finding or an enclosing `submission`
   object. Both new and existing models are supported. Multiple audits of the
   same axis are allowed; each submission is separate and does not overwrite
   an existing audit. Follow the schema's access requirements if credentials
   are required.
5. Save the returned `submission_id`, exact `status`, `receipt_token`, and
   `status_url` privately. `pending_review` means queued for review, not
   accepted or published; the receipt reports `published: false`.
6. To check status, `GET` the returned `status_url` or
   `/api/submissions/{id}` on https://spectra.yashaektefaie.com with
   `Authorization: Bearer <receipt_token>`. Use the ID and token from the
   receipt. Do not put the token in a URL, public artifact, or audit card.

Report the server's actual response. If validation fails, access is unavailable,
or a request's outcome is uncertain, preserve the prepared bundle and explain
what remains unresolved. Retry a submission only with the same idempotency key
and unchanged body. Do not claim submission or publication succeeded without
confirmation from the server. Review and publication are separate steps.

## Access

Reading the protocol and registry requires HTTPS `GET` access. Executing an
audit also requires the agent's tools, compute, data, and relevant model access.
Submission requires a client able to send HTTPS `POST` requests with a JSON
body and to set the authorization header for receipt status checks. If the
agent can only browse read-only pages, prepare the bundle locally and report
the missing HTTP capability. No connector configuration is required.
