# SPECTRA Finish Review

Version: 2026-10-29.1

Run this review-and-execution loop in the current session before any final
response. Do not wait for the user to paste it again. If useful, required work
is feasible, execute it, update the evidence, and repeat this review. A report
correction, a failed test, or one completed follow-up does not finish the loop.

In a broad audit, keep constructing and testing scientifically plausible
hypotheses until at least one generalizability axis has replicated on an
independent other dataset and meets the remaining completion criteria, or an
evidenced hard stop applies. Every positive candidate requires this external
replication, including predeclared and bounded predictive findings. A negative
axis, an exhausted initial hypothesis list, or a completed report does not complete the
search. Adapt the next experiment to the compute and data actually available.
Preserve honest negative results; never manufacture a positive finding.

`prompt.md` means the audit protocol you followed, normally your saved copy of
[protocol.md](https://spectra.yashaektefaie.com/protocol.md). If it is missing,
read that URL. Record the protocol and finish-review versions used. Keep the
user's scope and actual resource limits fixed. Preserve each frozen experiment's
success criteria and historical result. External replication is an additional
acceptance gate: an earlier single-dataset success remains discovery-supported
until it passes this gate; do not rewrite its original test or call replication
an optional extension.

## 1. Review claims against actual evidence

Reread the user's request, prompt.md, the axis ledger, frozen specifications,
and result tables. Do not accept your previous conclusion, a completion flag,
or a report's claim of exhaustion as evidence.

Maintain a compact `finish_review.md` in the run workspace, linking to existing
artifacts rather than duplicating them. Keep a row for every required criterion
and unresolved claim, including promising axes previously rejected:

| Claim / requirement | Effective distinct levels / independent support | Retained signal and failed component | Status and artifact evidence | Next concrete action |
|---|---|---|---|---|

Distinguish discovery-supported, externally replicated/accepted, adequate
non-replication, inadequate/inconclusive, open, and blocked. Track panel validity
separately from the scientific hypothesis. A positive discovery result alone is
not an accepted axis. Check:

- **Actual levels:** count meaningfully distinct similarity values and ties,
  and identify independent units or clusters appropriately. Do not infer the
  number of levels from the number of contexts, rows, or bin names. Four contexts
  at two values are two levels. A multi-level SPC requires at least three
  effective levels and sufficient resolution/support for its specific claim.
  Missing levels or power make evidence inadequate or inconclusive, not a
  scientific negative. Repair or replace the panel when feasible.
- **Exact claim:** distinguish predicting differences between entities from
  predicting changes within an entity. Determine whether each adjustment
  diagnoses a nuisance or changes the question. A within-gene sign reversal
  does not automatically erase a prospective between-gene signal. Check
  structural leave-one-out effects, leakage, artifacts, and deployment relevance.
  A replicated predictive association need not establish a causal mechanism;
  this distinction does not waive external replication for a bounded predictor.
- **Surviving signals:** preserve the failed original test or conjunction and
  identify what remains supported. A defensible narrower claim chosen after
  outcomes remains exploratory until newly frozen and replicated on an
  independent other dataset unused in its development.
  Do not discard a promising axis because a different claim failed, or delete
  the failed criterion to certify it on the same data.
- **External replication:** apply section 2 to every positive candidate. Verify
  the frozen direction, metric, levels, claim-aligned controls, independent
  support, numeric power/precision target, curve stability, baselines,
  provenance, and outcome-exposure history on both datasets. Shared baseline
  degradation is not automatically a confound; shared artifacts are.

A nonsignificant result alone does not refute a claim. An adequate negative
closes the precise axis-specific question; it routes a broad audit to another
plausible hypothesis. External replication is always required to accept a
positive axis. Distinguish genuinely optional extensions from that requirement,
and do not narrow the question to the released scores or initial candidate list
merely to declare completion.

## 2. Require external replication before accepting any positive axis

For each discovery-supported candidate, identify discovery dataset A and an
independent other dataset B. Execute replication on B before accepting the axis.
Predeclaration, a bounded predictive interpretation, a holdout from A, within-A
expansion, a corrected rerun, or a different checkpoint on A does not waive or
satisfy this requirement.

Add a compact replication record to the claim ledger or link an existing one:

| Candidate / exact claim | Dataset A and discovery result | Dataset B and independence evidence | Outcome exposure and frozen replication plan | Both curves, statistics, validity checks | Replication disposition and next action |
|---|---|---|---|---|---|

Require all of the following before acceptance:

1. **Independent evidence.** B must provide separately generated observations
   unused in axis development, tuning, or selection, including prior runs and
   pilots. A renamed dataset, mirror, derived table, or new split of A's
   underlying observations does not qualify. Record dataset lineage, collection
   provenance, exact and near-duplicate overlap, shared entities/clusters, and
   prior outcome exposure. Shared entities in independent experiments may test
   a declared transport claim, but cannot establish generalization to unseen
   entities. Derive overlap checks from actual identifiers and inputs; do not
   accept a stored independence flag without its evidence.
2. **Compatible comparison.** Verify that B can test the same frozen claim,
   axis definition, metric and intended similarity range with sufficient levels,
   independent support, labels, baselines and controls. Use the same frozen
   target checkpoint where compatible. A different checkpoint is allowed only
   when the predeclared claim expressly covers that model family or training
   recipe; verify its own split and inputs. Do not substitute a different model,
   task, or incomparable axis and call it replication. Incompatibility is an
   inadequate panel, not a negative scientific result.
3. **Frozen replication plan.** Before accessing B's target outcomes or scores,
   save the exact claim, feature formula and reference-source rules, direction,
   metric, permitted input mappings, level rule, scientific units and clusters,
   inclusion/exclusion and deduplication rules, meaningful effect, numeric power
   or precision target, baseline, claim-aligned controls, success/failure rules,
   and multiplicity or sequential-testing plan. Document how the frozen rule
   applies across A and B; do not tune it to B's outcomes. Select B using
   prospective suitability criteria and declare the primary replication dataset
   or multi-dataset decision rule before scoring.
4. **Executable validation and results.** Reconstruct independence/overlap and
   actual split/source membership from the underlying evidence, pass the
   pre-scoring level/support gate, then run or load the compatible target model's
   results and fixed baseline on all frozen levels. Cached scores are allowed
   only with verified provenance and exposure history. Save both A and B curves,
   per-level values/counts, uncertainty, effect statistics and controls, plus
   the scripts, timestamps and results of the validation checks. A saved PASS,
   matching hashes, or a report's assertion of replication is insufficient.
5. **Decision and routing.** Accept only an externally replicated axis whose B
   result meets the frozen replication criteria and validity gates. An adequate
   non-replication rejects acceptance of that claim: preserve A and B and move
   to another plausible axis. Invalid or inconclusive evidence also prevents
   acceptance, but is not automatically refutation; execute a bounded repair or
   expansion under the prespecified sampling/error-control plan when feasible.
   An outcome-informed change to the claim or axis creates a new discovery
   hypothesis and requires another independent dataset unused in its development.
   If replication is blocked, retain the candidate as provisional and pursue
   another feasible axis or a concrete data-access/compatibility probe.

Do not shop among datasets, discard failed attempts, change thresholds, or
reuse inspected replication outcomes until something passes. Preserve every
attempt and its exposure history. A valid, adequately precise non-replication
cannot be relabeled a pilot to seek a favorable B. A corrected rerun can repair
a validity error but cannot replace the required independent other dataset.
Apply the frozen error-control plan to any permitted sequential expansion or
multiple replication datasets. If no replication passes, no positive axis is
accepted, even when scientific refutation is not justified.

## 3. Recheck actual training splits and source inputs

Independently verify the protocol's actual-split/source-membership gate for
every panel, model variant, and baseline supporting the claimed finding. Use
the original split evidence and actual analysis inputs, not only the report,
the feature-construction script's own source labels, or a generic `PASS`.

- Bind each score file to its exact checkpoint/revision and effective training
  split/fold. Check configuration overrides and loader behavior. Distinguish
  separate leave-one-context-out models from one jointly held-out test set.
- Reconstruct source membership at the relevant sample/context/perturbation/
  dose granularity. Verify that sources described as training responses truly
  belonged to that model's training set. Other test contexts remain test data
  even when the current target is excluded. Availability of unperturbed
  controls does not imply availability of perturbation-response labels.
- Create or rerun an executable check over all actual feature and baseline
  sources using authoritative split evidence. Assert complete source coverage;
  retain unmatched or ambiguous keys as unknown, and reject an empty join when
  sources were used. Inspect the saved `split_audit.json` or equivalent
  mappings, role counts, violations, unknowns, and output-to-model bindings.
  Hash consistency, excluded column names, and saved success flags do not prove
  membership. Use metadata or bounded reads where sufficient; do not assume a
  large retraining job is needed just to verify or repair source selection.

Wrong membership invalidates the affected training-based test; unknown
membership leaves it unverified. Both prevent certification of a claim that
requires known training membership. These are input-validity requirements,
not optional stronger hypotheses. A declared external-reference or estimated
pretraining-proximity claim needs its own evidence and uncertainty; current
test responses cannot be renamed as an external reference after outcomes to
certify the original training-only claim.

If the check fails, reopen the affected claim and dependent confirmation or
baseline conclusions, while preserving valid evidence from other panels.
Identify or fetch eligible sources, rebuild the feature/baseline, rerun the
membership and similarity-level gates, and execute the corrected test when
feasible. Preserve outcome-exposure history: a revised axis or information set
chosen after inspecting outcomes must be frozen and externally replicated on
an independent other dataset unused in that revision's development. A repair
on A does not satisfy the external-replication gate for the repaired candidate.
Changing a status or adding a caveat does not complete the repair. If this
route is genuinely blocked, keep its evidence and pursue another feasible axis.

## 4. Design the next test around available resources

Ask: "What scientifically useful experiment can I run with the resources I have?"
Inspect actual available capacity and workloads, free memory/disk, authorized
cache/output paths, checkpoints, cached predictions, processed data, and access
constraints. Installed hardware alone does not establish usable capacity.
Reuse recent measurements unless conditions have changed.

For each unresolved required claim or criterion, identify a concrete next action
with inputs, an expected artifact or decision, a decision rule, and a bounded
resource allocation. Examples include inspecting a processed-data schema,
measuring distinct prospective levels, identifying an independent replication
dataset, checking checkpoint compatibility, or running a representative
inference/timing probe. "More research" or "a new training study" is not an
executable next action.

If the preferred experiment is too expensive, inspect cheaper scientifically
valid routes: existing target-model outputs, aggregate/processed datasets,
selected data ranges, smaller balanced panels, sequential execution, compatible
checkpoints, or bounded fitting. Measure feasibility when it is unknown. A
paper's largest training configuration does not establish the minimum cost of
the audit. A small probe may justify the next step without being enough to
certify a curve; do not substitute a different model or an inadequate proxy
and claim it answers the original target-model question.

If an axis truly requires unavailable training or data, retain its specific
blocker and move to another plausible axis that fits the available resources.
Use accumulated successes and failures to generate new prospective hypotheses;
search for or construct accessible evidence when the current pool is inadequate.
Completing the initial hypothesis list does not end discovery.

## 5. Challenge every proposed stopping reason

For each blocked route, record the exact obstacle and observed evidence, cheaper
or alternative approaches considered and their results, the actual limit and
its source, and why another bounded useful step cannot proceed. Unknown
feasibility calls for a bounded check when possible; if that check enables work,
execute it. One expensive training proposal cannot block the whole audit.

Separate user/system limits and observed constraints from per-step allocations
you chose yourself. A timeout triggers a fallback or redesign. Absence of a
stated total budget is not exhaustion and cannot justify stopping bounded work
already within the authorized task. It also does not authorize new spending,
commandeering occupied resources, or unlimited computation. Respect actual
limits and authorization; identify a specific needed permission only when the
next action requires it. Continue independent feasible work meanwhile.

Current-pool exhaustion, many failed hypotheses, elapsed effort without an
actual time cap, or "a separate study would be needed" is not sufficient stop
evidence. Assess all live claims and credible next routes, including another
testable hypothesis. You need not disprove every imaginable experiment, but
cannot ignore a concrete feasible route merely because it requires more work.

## 6. Execute, update, and repeat

If a required item has a feasible authorized next action, perform it now.
Prioritize executing external replication of promising signals and resolving
completion-critical uncertainty. When those steps are blocked, execute another
useful hypothesis test, data or
feature construction step, or feasibility probe. Do not stop at an apology,
future-work list, or statement that more compute would help.

After every discovery or replication test, split-membership failure, feasibility
check, or report correction:

1. Update the claim ledger and A/B replication record with actual results,
   exposure history and the precise decision; discovery success alone cannot
   enter the accepted state.
2. Rebuild the concrete next-action queue, generating a new plausible hypothesis
   when needed rather than treating an empty initial list as completion.
3. If required work remains, execute the highest-value feasible authorized
   action; otherwise assess the final-response gate.
4. Repeat this entire finish review before considering a final response.

Record each cycle's action, resulting evidence, decision, and next action
compactly in the existing log, with actual execution timestamps and commands.
Distinguish scientific work performed before this review from work triggered by
it; do not present a retrospective summary as new review-and-execution cycles.
Every cycle must add evidence, resolve a specific uncertainty, or establish a
supported blocker. Rewriting conclusions,
checking unchanged resources repeatedly, or retrying unchanged failures does
not count. Save the ledger, outcome-exposure history, and next action across
context compaction.

Keep discovery adaptive and external replication disciplined. Freeze every
replication plan before accessing its outcomes and preserve all attempted
hypotheses/results. Use the protocol's error-control plan across repeated
attempts. Do not re-slice outcomes, change endpoints, or reuse a holdout until
something passes. A finish cycle must execute the next feasible required action,
not merely recommend finding another dataset and stop.

## 7. Final response gate

Give a final response only when one of these conditions holds:

- **Complete:** the user's completion criteria and this external-replication
  gate are met by saved evidence, and no required item is unresolved. In a broad
  audit this requires at least one externally replicated explanatory/degradation
  axis: name datasets A and B and cite the frozen plan, independence evidence,
  executable validity checks, both curves and their statistical results. A
  single-dataset result cannot complete a positive audit, even if predeclared,
  bounded, or repaired. External replication is never optional for acceptance.
  An explicitly axis-specific negative task may finish with an adequate negative
  result answering that precise question; this exception cannot certify a
  positive axis or complete a broad discovery audit.
  The actual-split/source-membership checks must pass for every panel and
  baseline needed to support the claimed result; no required membership may
  remain wrong, unknown, or assumed from excluding only the current target.
  Once these criteria are met, exploratory alternatives unnecessary to
  support the completed claim may remain ledgered without further testing.
- **Incomplete, demonstrated hard stop:** required work remains, but an actual
  enforced limit or evidenced obstacle leaves no useful feasible authorized
  next action. Cover each remaining concrete route and its credible cheaper
  alternatives, including another testable hypothesis; cite limits, probes,
  results, and unresolved claims. Do not call this scientific completion or
  evidence that no failure axis exists.
- **User-directed stop or checkpoint:** honor the instruction and state what
  remains unfinished.

If none applies, continue execution and review without asking the user to tell
you to continue. At a justified final response, state the status and cite the
saved review and decisive evidence concisely.
