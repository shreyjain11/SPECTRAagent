# Submit an AutoSPECTRA audit

Use this route when the user asks to submit a completed audit. Reading these
instructions alone does not authorize submission or publication. For running
or finding audits, use the [agent guide](./agents.md).

Send all API requests below to https://spectra.yashaektefaie.com, including
when reading this guide on GitHub or in a local website preview. Document
links are relative to this guide. The client must support HTTPS requests with
JSON `POST` bodies and authorization headers. No connector setup is required.

## 1. Read the contract

`GET` the [current submission schema](https://spectra.yashaektefaie.com/api/submissions/schema). Check the
returned contract, queue availability, access requirements, and request-size
limit. Use the server's current schema rather than assuming the examples or
requirements have remained unchanged.

The request body is the full existing submission bundle, including:

- `title` and `submitter`, with the required name and contact information.
- `finding`, including model, task, axis definition, performance evidence,
  validity decision, claim boundary, and limitations.
- `provenance`, recording the model/checkpoint, datasets, retrieval, and
  execution environment.
- `downloads` and `artifact_manifest`, connecting the results to their
  supporting artifacts.
- `audit_card_markdown`, containing the readable audit card.

Use the schema's required fields and example to construct these objects. Send
this bundle itself as the JSON body, without a surrounding `submission` key.
Do not send only a finding, a report path, or a short card summary. Do not set
reviewer-owned acceptance or publication fields yourself.

New models and existing models can both receive submissions. Multiple audits
can examine the same axis of the same model. Use identifiers that distinguish
the submitted audit and its evidence from existing records, preserving model
and axis identity accurately. Submission creates a separate record; it does
not replace or overwrite an existing audit.

## 2. Prepare the evidence

Preserve the actual result, including negative or inconclusive conclusions and
known limitations. Never fabricate measurements, provenance, or confirmation
to satisfy the contract.

Large result tables, figures, and model outputs should remain at stable public
HTTPS URLs. Record their SHA-256 checksums, byte sizes, and row counts where
applicable. A local path or a link accessible only on the agent's computer is
not a public download. Keep the request within the advertised JSON size limit.

If hosting or required evidence is missing, identify the missing prerequisite
and save the prepared bundle locally. Do not upload private files without the
user's authorization. A request to submit a card does not make every file in
the workspace appropriate for public sharing.

## 3. Validate

Send the full bundle to [validation](https://spectra.yashaektefaie.com/api/submissions/validate):

```http
POST /api/submissions/validate
Content-Type: application/json

<full submission bundle as JSON>
```

Inspect the returned validation result. Correct contract errors and address
warnings using the available evidence; record genuine gaps instead of hiding
them. A successful validation checks the submission contract. It is not a
scientific review, a submission receipt, or a publication decision.

## 4. Submit for review

For a user-authorized submission, send the validated bundle to
[submissions](https://spectra.yashaektefaie.com/api/submissions):

```http
POST /api/submissions
Content-Type: application/json
Idempotency-Key: <unique key for this submission>

<the same full submission bundle as JSON>
```

Create and save one idempotency key for this submission. Reuse the same key
and unchanged body when retrying that request so a network retry does not
create another submission. Use a new key for a separate audit.

Follow the access requirements returned by the schema. If submissions require
credentials, ask for or use the user's authorized access; an HTTP `401` is not
a successful submission. Submission credentials are separate from the receipt
token returned after success.

On success, the response includes `submission_id`, `status`, `receipt_token`,
`status_url`, and `published`. Save the receipt privately in the user's
workspace. Report the ID and exact status to the user. `pending_review` means
the audit is queued for review; it does not mean accepted or published.
`published: false` confirms that this receipt is not a publication event.
Do not expose the receipt token in an audit card, public artifact, URL, or
ordinary status summary.

If the server rejects the request, report the actual reason. If a connection
failure leaves the outcome unknown, retry only with the saved idempotency key
and unchanged body, or report the uncertainty. Do not claim success without
the server's confirmation.

## 5. Check the receipt

Use the returned `status_url`, or the submission ID on
https://spectra.yashaektefaie.com:

```http
GET /api/submissions/{id}
Authorization: Bearer <receipt_token>
```

Use the receipt token in the header, not in the URL. Report the returned
status and review feedback accurately. Only describe an audit as published
when the server confirms publication; acceptance and publication are distinct
outcomes. Retain the submitted bundle and receipt so the user can check again
later.
