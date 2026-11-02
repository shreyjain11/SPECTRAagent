# AutoSPECTRA: agent guide

Use AutoSPECTRA to run a generalizability audit, find a prior audit, or submit a
completed audit. Choose the route the user requested. Reading this guide alone
does not request an audit or authorize publication.

If the user shares this guide without a specific goal, briefly offer the three
routes and ask which model or completed audit they have in mind. Use any intent
already present in the conversation instead of asking them to repeat it.

## Run an audit

1. Identify the target model and the user's question. Use the available compute,
   data, access, and runtime limits; ask only for information needed to proceed.
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

## Find a prior audit

Read the public [findings index](https://spectra.yashaektefaie.com/data/findings.json).
Search its `findings` by model, task, domain, and axis. For relevant records,
inspect the claim boundary, evidence status, limitations, provenance, and linked
downloads. Return the finding IDs and the evidence links that support the answer.

If the AutoSPECTRA MCP connection is available, use `search_spectra_findings` or
`list_spectra_findings`, then `get_spectra_finding`, `get_spectra_provenance`, and
`list_spectra_downloads` as needed. Download full tables from the returned HTTPS
URLs; artifact previews may be truncated.

Distinguish a registry record's reported status from a new independent check.
Do not treat different versions or checkpoints as interchangeable. If no relevant
record is found, say so; absence from this registry does not establish that no
audit exists elsewhere. A request to find an audit does not require running one.

## Submit a completed audit

Submission uses the [MCP endpoint](https://spectra.yashaektefaie.com/mcp).
Inspect the tools exposed by the connected server rather than assuming a local
installation and the hosted service have identical capabilities.

1. Call `get_spectra_submission_schema` for the current contract and queue status.
2. Prepare the finding, provenance, download records, artifact manifest, and audit
   card required by that schema from the user's completed audit. Preserve its
   actual results and limitations. Do not invent missing evidence to satisfy a
   field or change a conclusion to obtain acceptance.
3. Supporting files must already be accessible at stable public URLs where the
   contract requires them, with their checksums, byte sizes, and row counts.
   A local path is not a public download. Report missing hosting or evidence as a
   concrete prerequisite; do not upload private data without the user's permission.
4. Call `validate_spectra_submission` and resolve the reported contract errors.
5. For an authorized submission, call `submit_spectra_finding` if the hosted
   server exposes and permits it. Follow the host's authentication requirements.
   If the connection or required credentials are unavailable, save the prepared
   bundle and report what access is needed. Do not claim submission succeeded.
6. Report the returned submission ID and exact status. `pending_review` means
   submitted for review; it does not mean validated, accepted, or published.
   Publication is a separate outcome and must be confirmed by the server.

## Connection

Reading the protocol and public findings index requires HTTPS access. Executing
an audit also requires a coding agent with suitable tools, compute, data, and
model access. Submission requires an MCP-capable client connected to:

`https://spectra.yashaektefaie.com/mcp`

Use the client's supported setup for a Streamable HTTP MCP server. Authentication
and tool availability depend on the hosted service; never expose credentials in
an audit card or public artifact.
