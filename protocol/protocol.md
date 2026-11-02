# SPECTRA Generalizability Protocol

Version: 2026-11-02.1

This service exposes SPECTRA guidance and published findings over HTTPS, and
accepts contributed audit cards into a pending review queue. Audits run in the
user's agent environment; the service does not execute model evaluations.

## Purpose

Treat SPECTRA as a spectral performance curve construction and validation
workflow. The primary product is model performance as prospective train-test or
pretraining-test similarity decreases, plus an explicit validity assessment.

For broad prompts such as "assess the generalizability of this model", first
extract the model paper's stated and implicit generalization claims and use
those claims to seed the hypothesis ledger. If the scope is beyond the paper,
use the paper as model context but search for or construct public/local datasets
that test important external generalization axes.

In a broad audit, keep constructing and testing scientifically plausible
hypotheses until at least one axis is supported on its development dataset and
replicated on a genuinely independent other dataset unused in developing,
selecting, or tuning that axis, with the user's completion criteria met; or the
user requests a stop; or an evidenced hard stop applies. Every positive axis
requires this replication, including predeclared and bounded predictive axes.
A first successful test is discovery support, not acceptance or completion.
A negative axis, an exhausted initial hypothesis list, or a completed report
does not finish this search. Adapt experiments to available authorized compute
and data; after an unsuccessful test, use its evidence to choose and execute the
next useful test. An explicitly axis-specific task may close with an adequate
negative result. Preserve honest negatives and uncertainty throughout; continued
search never licenses manufacturing a positive result.

## Controller Loop

Use one persistent controller process for an audit. Dataset state,
target-model results, prospective features, the axis ledger, negative results,
and validation decisions should stay in one shared state. Distiller,
Investigator, Dataset Scout, Dataset Fetcher, and Auditor are phases of the
same loop, not separately routed agents unless a host client explicitly needs
that decomposition.

The loop is:

1. Distill the user question into a model, task, metric, scientific unit,
   deployment population, exact comparison, prospective axes, and SPC plan.
2. Inspect usable resources and scout or fetch data needed for the live claim.
3. Bind each scored model to its actual training split and pass the source-
   membership gate below; then construct prospective similarity levels.
4. Pass the pre-scoring panel gate, including effective distinct levels and
   independent support, and verify decreasing measured similarity.
5. Run a simple fixed baseline when labels exist.
6. Score the frozen panel. Exploratory feasibility probes are allowed. Panel
   inadequacy alone is not scientific refutation; a valid lower-resolution
   contrast retains its bounded interpretation and cannot certify curve shape.
7. Audit the evidence against the exact claim; distinguish a nuisance control
   from a test that changes the comparison being estimated.
8. Update the claim ledger and next-action queue. For every supported candidate,
   scout a compatible independent dataset unused in axis development, freeze and
   execute replication, and accept only if that replication passes. Otherwise
   follow the non-replication, inconclusive/invalid, or blocked route below and
   continue the search. Repair inadequate panels or construct the next plausible
   axis. If a step exceeds available compute, redesign it or pursue another
   feasible axis. One blocked experiment does not block the audit.
9. Before any final response, execute the review in
   [finish.md](https://spectra.yashaektefaie.com/finish.md). If useful authorized
   work remains, perform it and repeat the review without waiting for another
   user prompt. Stop only under that review's final-response gate.

## Roles

SPECTRA Distiller turns user generalizability questions into SPECTRA analyses.
It identifies or validates candidate similarity axes that could yield meaningful
SPCs, interprets results, distinguishes valid from exploratory axes, avoids
overclaiming, and routes negative or weak results back into discovery.

SPECTRA Investigator executes the protocol for a model, dataset, task, metric,
and similarity axis. It computes prospective similarities without target-model
errors, requires at least three effective distinct levels for a multi-level
SPC, verifies decreasing similarity, runs fixed baselines when labels exist, then
evaluates the model of interest. Small bounded model runs are pilot probes, not
valid SPC evidence, unless they cover the full split or a predeclared adequately
powered stratified evaluation sample.

SPECTRA Dataset Scout finds datasets suitable for SPECTRA. It prioritizes
datasets with labels, metadata, prospective similarity features, enough examples
for multiple split levels, clear access, and low leakage risk.

SPECTRA Dataset Fetcher retrieves and packages datasets for SPECTRA. It retains
inputs, labels, metadata, and prospective features, handles duplicates and
missingness, and creates SPECTRA-ready artifacts. For very large pretraining
datasets, it should use bounded filtering or approximate retrieval rather than
exhaustive comparison. It must also record source provenance: data source URL
or repository, split/shard/filter details, unit of analysis, row or unit count
when known, local/cache path, download or access command, and license or access
constraints when relevant.

SPECTRA Auditor checks whether the SPC supports the claim. It looks for
target-error leakage, test-label leakage, tiny splits, non-decreasing
similarity, unstable baselines, confounding, post-hoc axis selection, pilot-only
target evaluation, and outcome-informed axis discovery. It records panel
validity separately from the scientific claim's disposition. Insufficient
levels, power, or coverage mean inadequate or inconclusive evidence, not a
refuted hypothesis.

## Axis Rules

Do not use target-model errors, prediction-versus-reference errors, held-out
labels, target confidence derived from the evaluated model, or other
outcome-dependent quantities to define a similarity axis or split membership.
Post-hoc failure characterization can suggest hypotheses, but those hypotheses
are exploratory until frozen and confirmed.

Do not claim a SPECTRA split is valid unless measured cross-split overlap or
pretraining-test proximity decreases across the spectral parameters.

Preserve failed or non-monotonic results in the ledger. Identify exactly which
claim failed and what evidence remains informative before deciding whether to
repair the panel, confirm a surviving signal, or test the next scientifically
plausible prospective axis. Do not discard a whole axis because one stronger
claim failed, and do not retroactively turn the original failed test into a pass.

Select the strongest scientifically defensible, leakage-aware novelty axis, not
merely the most monotonic curve.

## Claim and Control Contract

Before choosing controls, freeze the deployment question, population, scientific
unit, independent sampling or clustering unit, and what varies in the comparison.
Distinguish a predictive association between entities (which genes transfer
better), a within-entity association (which held-out context is easier for the
same gene), and a causal or mechanistic claim. Evidence for one does not
automatically establish or refute the others.

For each mandatory control or sensitivity test, state whether it diagnoses a
nuisance affecting the declared claim or tests a different, stronger claim.
Entity fixed effects remove between-entity information: a within-gene reversal
does not by itself invalidate a prospective between-gene predictor. Conversely,
a between-gene curve cannot answer a within-gene deployment question. Check
whether rotating held-out contexts, overlapping training sets, or complementary
leave-one-out construction creates structural relationships in the diagnostic.
Keep the original preregistered conjunction and its result unchanged.

A surviving predictive signal still needs leakage, metric-artifact, nuisance,
and deployment-relevance checks. A batch or dataset identifier that only works
because of the sampled population is not thereby a transferable predictor.
Shared degradation in a fixed baseline can characterize general task difficulty;
it neither automatically invalidates the axis nor excuses an artifact.

## Actual Training Split and Source-Membership Gate

Verify the information available to the exact scored model before constructing
the axis or baseline and before accepting cached results as confirmation.
Excluding the current target does not establish that the remaining sources are
training data. Apply this gate separately to each discovery/confirmation panel,
checkpoint, and fold used to support the finding.

1. **Bind scores to the effective training split.** Link each scored output to
   its checkpoint identifier/revision, dataset revision, training or fine-tuning
   run, and resolved split/configuration. Inspect checkpoint-linked manifests
   or equivalent authoritative evidence, configuration overrides, and relevant
   loader/filter behavior. Establish whether contexts were held out individually
   in separate models or jointly from one model. Different result filenames do
   not prove different training folds; a paper diagram, repository template, or
   generic dataset name cannot substitute for this binding. Resolve conflicting
   evidence or record the binding as unknown.
2. **Trace every actual source.** For axis features, level assignments, and
   baseline predictions, record the source identifiers at the relevant unit:
   sample, donor, context, perturbation, dose, or other task-specific keys. Trace
   derived response summaries to their contributing records. Classify sources
   as documented training inputs, validation/test information, explicitly
   permitted external references, or unknown. Distinguish raw/basal inputs,
   unperturbed controls, and perturbation-response or other outcome labels.
   Context membership alone is insufficient for a few-shot split; access to
   control cells never establishes access to perturbed-response labels.
3. **Compute membership assertions.** For a training-only response feature,
   assert that every response-label source used belongs to the effective
   training set for that checkpoint and fold, after overrides and exclusions.
   Apply the declared information restrictions to the baseline as well. Test
   the full source set, including other members of a joint holdout, rather than
   checking only `source != current_target`. For example, if five contexts are
   jointly test-only, using four to predict the fifth fails this gate. If each
   target has its own leave-one-context-out model, verify the other four against
   that model's own split before allowing them. Assert coverage of every actual
   source record: retain unmatched or ambiguous keys as unknown, never silently
   drop them, and reject an empty membership join when sources were used.
4. **Save executable evidence.** Keep a compact `split_audit.json` or equivalent
   manifest containing output-to-checkpoint/fold bindings, authoritative split
   and loader references with revisions/hashes, declared information roles,
   source mappings or reproducible joins, counts by membership, unmapped or
   ambiguous keys, violations, and the command that produced the check. The
   validator must derive eligibility from the split evidence and actual inputs;
   it must not merely echo saved success flags or source labels assigned by the
   analysis script. Hashes, column-name exclusions, and a sampled spot check
   alone do not establish full source membership. Use metadata/manifests and
   bounded reads where sufficient; this gate does not require loading an entire
   training corpus or rerunning training just to inspect its split.

Unknown membership is not proof of leakage, but it cannot pass a claim requiring
known training membership. Investigate accessible manifests, configs, or loader
rules; keep any remaining uncertainty explicit. An estimated pretraining-
proximity or external-reference claim may be defensible with its own declared
information access and uncertainty, but cannot claim verified training exposure.
External references must have a justified deployment role and availability;
never relabel the current evaluation set's held-out responses as external data
after seeing a favorable curve to rescue the same training-only claim.

Wrong or unverified source membership is a validity failure or unresolved input
requirement, not an optional stronger scientific claim or a negative result
about the axis. Withhold certification of the affected claim and any conclusion
that depends on the invalid baseline or confirmation. Preserve unaffected
evidence and the original result, identify eligible sources, then execute a
repair: rebuild the feature and baseline, rerun membership and level gates, and
evaluate the corrected frozen test. If repair changes the axis, reference pool,
or comparison after outcome exposure, treat that as discovery, freeze the new
claim, and obtain independent confirmation. A rerun on already inspected outcomes
can diagnose the repair but does not become fresh confirmation. If repair is
blocked, document that specific obstacle and pursue another feasible axis.
Adding a caveat or changing the report's status is not a substitute for this work.

## Pre-scoring Panel Gate

First pass the source-membership gate for this panel's actual checkpoint/fold,
including baseline inputs; a membership failure cannot be waived by adequate
level counts or a strong curve. Before accessing confirmation outcomes, record
the prospective axis values and level assignments. At the intended scientific
and independent sampling units,
report the effective number of distinct values at a prespecified numerical or
measurement resolution, their range and ties, the per-level value distribution,
independent units or clusters per level, and context/source coverage. Confirm
that the proposed test can resolve the prespecified effect at the planned
uncertainty or power; many correlated rows do not create independent support.

A multi-level SPC requires at least three meaningfully separated, populated
levels with adequate independent support. Four contexts with two distinct
similarity values are a two-level comparison, not a four-level curve. Repeated
rows, split ties, artificial jitter, quantile labels, or negligible floating-point
differences cannot create extra levels. Three levels are a minimum gate, not
sufficient resolution for every continuous or localized claim.

If the panel fails this gate, mark it inadequate for the intended claim and
expand or replace it before confirmation. A binary contrast may be reported
with its limited interpretation; it does not establish multi-level curve shape.
Do not label missing levels or insufficient power a negative scientific result.
If the defect is discovered after scoring, retain those results as exploratory,
freeze the repair, and obtain fresh confirmation evidence for an outcome-informed
revision. Never silently alter bins after seeing performance.

## Mandatory Independent-Dataset Replication

Every positive axis, including one completely predeclared before its first test,
must pass this gate. A supported curve on development dataset A is
`discovery-supported`, not accepted or certified. A within-A holdout can validate
the initial test but cannot replace replication in another dataset B. Bounded
predictive claims have the same replication requirement as other positive claims;
replication does not require proving a causal mechanism.

### Independent data and compatibility

After finding a candidate, scout, obtain, and evaluate a compatible independent
dataset. "New" means independently generated observations unused in developing,
selecting, or tuning the axis, not merely a new download or filename. A mirror,
renamed release, derivative table, resplit, extra shard of the same development
dataset, rerun on inspected observations, or new checkpoint on the same data does
not satisfy this gate. A dataset already used to revise the axis is development
evidence for that revision, even if it originally began as replication data.

Record dataset identity, version, collection/experimental lineage, scientific
units, exact/near-duplicate and leakage-linked overlap, shared entities, and prior
outcome exposure across runs and attempted axes. Different dataset names are not
proof of independence. Separately collected experiments on the same compounds,
genes, or other entities may test transport across datasets, but cannot establish
unseen-entity generalization. Explain why independence matches the frozen claim;
remove dependent records and assess support at the actual independent units.
Unknown lineage or unresolved material overlap blocks acceptance.

Select B using task/schema/metadata compatibility before inspecting its target
outcomes. Metadata-only screening and applying the already frozen axis are
allowed; using B to develop or tune the feature consumes it as development data.
The panel must test the same scientific comparison and deployment scope, provide
compatible inputs and labels, and span the similarity range and curve regions
needed for the claim with adequate independent support. An incompatible panel
does not constitute a failed scientific replication. A new dataset does not by
itself prove model holdout: separately verify actual checkpoint-specific
training/validation/test membership and feature/baseline source restrictions.

Prefer the same frozen audited checkpoint. Do not silently change models, train
a surrogate, or redefine the task to obtain a positive result. If the declared
question concerns a model family or training procedure, specify any permitted
checkpoint variants, fitting, preprocessing, and input mappings before B outcome
access and bind each scored run to its own effective split. Such replication
cannot certify a fixed-checkpoint claim that it does not test. Use compatible
official cached outputs or bounded inference when available; fresh inference
alone is not evidence independence.

### Freeze, execute, and judge replication

1. Save A's original claim, curve, source of the hypothesis, frozen specification,
   result, and complete development/outcome-exposure history. Preserve the
   original result even if later replication fails.
2. Before B outcome access, save a replication specification that fixes the
   original axis formula and reference-source rules, direction, primary metric,
   baseline, exact comparison, model/checkpoint contract, and allowed input
   mappings. Freeze B selection and eligibility, exclusion/deduplication rules,
   scientific units and clusters, level-construction rule, claim-aligned controls,
   meaningful effect, a numerical power or CI-precision target, and success,
   non-replication, inconclusive, multiplicity, and sequential-stopping rules.
   Merely specifying a p-value cutoff is not a power or precision plan.
3. Independently pass B's actual-split/source-membership and pre-scoring panel
   gates. Record prospective values, effective levels, their range, counts,
   overlap checks, and adequate independent support before examining performance.
   Existing minimum-level rules apply; copying A's bin labels does not pass.
4. Execute the frozen test on B and save the full SPC, uncertainty, fixed baseline,
   controls, scored rows, and provenance. Reproduce the claimed relationship and
   a meaningful effect under the frozen rule, not merely a favorable point
   estimate or nominal p-value. Absolute performance need not equal A. A claimed
   threshold or localized curve shape needs enough relevant levels and data to
   test that shape; a pooled slope cannot substitute for it.
5. Judge B on its frozen rule without changing the feature, endpoint, direction,
   subgroup, level rule, comparison, or threshold after seeing the result.
   Applying a frozen metadata-based level rule to B is allowed; choosing a new
   rule because of B's curve is not. An outcome-informed revision becomes a new
   discovery hypothesis and requires another unused independent dataset.

Choose the primary replication dataset, or a multi-dataset decision rule, before
examining replication outcomes. Preserve all attempts and use the prespecified
error-control plan across datasets, candidate axes, and sequential expansions.
Do not shop for a favorable dataset, omit failed attempts, repeatedly inspect a
holdout, or keep sampling until something passes. A later positive result cannot
erase an earlier adequate non-replication. A broader synthesis or revised scope
requires its own explicit test plan and fresh evidence.

### Replication dispositions and next action

- **Replicated / accepted:** A supports the candidate and independent B passes
  the frozen replication rule and all validity gates. Certify only the scope
  tested across A and B.
- **Adequate non-replication:** a valid, sufficiently precise B test rejects the
  prespecified meaningful claim. Do not accept the axis. Preserve A and B, mark
  the claim non-replicated, and move to another plausible hypothesis; do not keep
  trying alternative datasets under the same claim until one passes.
- **Inconclusive or inadequate/invalid:** insufficient precision, range, levels,
  independence, compatibility, or membership does not pass and is not proof of
  absence. Execute a scientifically justified bounded repair or expansion under
  the prespecified plan when feasible. If the repair changes the axis or claim
  after outcomes, use fresh independent data. Otherwise retain provisional
  status and pursue another feasible candidate.
- **Blocked or unavailable:** no qualifying replication was executed. Retain the
  discovery signal as unaccepted, record the evidenced obstacle and attempted
  affordable routes, and move to another feasible axis. A lack of replication
  data is not a negative scientific result or a completion waiver.

"Not accepted" covers every nonpassing state; "contradicted" requires adequate
claim-aligned evidence. A nonsignificant p-value alone is not an adequate negative.
An explicitly axis-specific negative task may close with an adequate negative,
but a positive axis cannot be certified without independent-dataset replication.

Maintain the claim ledger with one row per candidate and attempted replication:

| Axis / frozen claim | Development dataset A and result | Replication dataset B / attempt | Independence and outcome-exposure evidence | Frozen replication spec / panel gates | Both SPCs and test results | Disposition | Next concrete action |
|---|---|---|---|---|---|---|---|

Preserve supported, contradicted, inconclusive, and invalid results within each
dataset separately from the overall acceptance state. Never silently rename a
single-dataset result "replicated" or recast required replication as optional.
For earlier runs evaluated under an older protocol, retain their historical
criteria and outcomes; classify single-dataset findings as discovery-supported
under this acceptance policy rather than rewriting their original tests.

## Runtime Policy

Treat available compute as an input to experimental design. Inspect actual
usable capacity, existing workloads, free memory and disk, checkpoints, cached
predictions, processed datasets, and the user's access/time/spending limits.
Installed devices are not proof of available capacity. Use the authorized cache
and output locations, estimate storage needs, and avoid filling them. Record
constraints compactly and refresh them when conditions materially change.

Ask: "What scientifically useful test can I execute with these resources?"
Before expensive fitting, fine-tuning, all-pairs construction, large indexing,
or full-dataset embedding, run the smallest representative leakage-aware probe
that resolves the next scientific or feasibility question. Estimate runtime and
memory from a measured probe when feasible, not solely from a paper's largest
training configuration.

Start with schema/leakage checks, simple controls, cached or chunked
representations, and deterministic non-iterative probes such as nearest
centroid scores, mean-difference linear scores, kNN/prototype retrieval, or
closed-form small linear baselines. Escalate only when the cheap probe is
inconclusive or the stronger deployment claim requires it.

Before a heavy step, record a bounded allocation, expected output, decision
rule, timeout, and cheaper fallback. If it does not fit, inspect processed or
aggregate data, selected ranges, existing checkpoints or official predictions,
smaller balanced panels, sequential execution, or bounded fitting where
scientifically applicable. Execute a useful feasible alternative rather than
ending with "a huge training run is required." A pilot can establish feasibility
without qualifying as a final curve. Do not substitute a different model or an
underpowered proxy and claim it answers the original target-model question.

If the current claim genuinely needs unavailable training, preserve it as
blocked with evidence and move to another plausible axis that can be tested
with available resources. After a timeout or runtime failure, use a revised
method or fallback; do not repeatedly retry unchanged failures. Acquiring new
data, prospective features, or a compatible checkpoint is an executable next
step when within scope and resources, not merely a future-work suggestion.

Separate actual user/system limits and observed constraints from allocations
you selected for individual steps. Absence of a stated total budget is not
budget exhaustion; continue useful bounded work within existing authorization.
It also does not authorize new spending, commandeering occupied resources, or
unlimited computation. A per-step budget cannot become a global stopping rule.

For every unresolved claim, keep a concrete next action with inputs, expected
artifact or decision, bounded resources, and any evidenced dependency. After
each result, repair, or feasibility check, update this queue and execute the
highest-value feasible action. Prioritize promising signals, but if their next
steps are blocked, pursue other plausible hypotheses. Each iteration must add
evidence, resolve an uncertainty, or establish a blocker; repeated report edits
and unchanged feasibility checks are not forward progress.

Maintain one reusable candidate/prospective-feature table. Prefer
manifest-first expansion, deduplicate or cluster near-duplicates before
expensive evaluation, avoid blind rejection sampling against external APIs, and
keep a persistent target-model evaluator loaded when feasible.

## Provenance Contract

Every paper-facing or registry-published SPECTRA finding must include normalized
provenance. A stored finding is incomplete unless an agent can answer:

1. Where did the model code come from?
2. Where did the model weights, checkpoint, or official precomputed scored
   outputs come from?
3. How were those weights or scored outputs downloaded, cached, or loaded?
4. Where did each dataset, split, shard, or candidate panel come from?
5. How was each dataset downloaded, filtered, deduplicated, or bounded?
6. Which metadata resources defined similarity axes, controls, labels, or
   claim boundaries?
7. Which local paths and artifact ids support the record?
8. What exact gaps remain, such as missing checkpoint revisions or legacy
   cache hashes?
9. Which effective training split and loader rules belong to each scored
   checkpoint/fold, and which executable membership evidence shows that the
   feature and baseline inputs obey their declared information restrictions?
10. Which independent dataset replicated the development finding, how was its
    lineage/overlap/outcome-exposure history checked, what plan was frozen before
    its outcomes, and where are both curves and every replication attempt?

For hosted knowledge-server findings, add or update the normalized provenance
record and validate it before publishing. If fresh inference was not run, say
so directly and record the official scored-result repositories/files instead
of pretending model weights were evaluated locally. If a legacy run lacks exact
download hashes or cache revisions, mark the gap explicitly and route to
backfill before claiming full reproducibility.

If a paper-facing or reviewer-facing claim requires re-running the analysis
from per-target or per-example rows, the raw scored tables must be published as
normal HTTPS downloads with byte size, row count, and SHA-256 checksum. Hosted
registry cards expose the download URLs and checksums in their `downloads`
records. Follow those URLs for complete evidence; summaries are not a bulk
transport mechanism.

## Closure Gate

Recompute the actual-split/source-membership checks for every panel and baseline
needed to certify the claim, using checkpoint-linked split evidence and the
inputs actually used. Any violation or unresolved membership required by the
claim blocks certification, even if its p-value, curve shape, and checksum
verification pass. Reopen dependent findings and execute the repair route above;
do not reclassify this validity requirement as an optional sensitivity.

Before final synthesis, the axis must use prospective features, with the axis
and replication plan frozen before accessing B outcomes or running new B scoring.
Retain outcome-informed work on A as development evidence; pre-existing cached B
outputs are allowed under the exposure/provenance rules above. The axis must be
measured in the intended order, adequately powered, densified
enough to characterize trend shape, stable under expansion or explicitly
reported as unstable (and not certified beyond that evidence), supported on
development dataset A and replicated on independent dataset B under the mandatory
gate above regardless of whether the axis was predeclared, attributable to the
declared predictive or other comparison rather than to a measurement artifact or a
nuisance confounder that would mean the axis is measuring something else,
characterized against a fixed baseline when labels exist to confirm the
degradation is real and to label it model-specific or shared rather than to
reject it (a real degradation that baselines or other trained models also show
is a valid finding and must not be rejected for being shared), and accompanied by model,
weights/checkpoint or official-score, dataset, metadata, download, cache, and
known-gap provenance. Persist every analysis artifact — the frozen-axis spec, SPC
tables, scripts, and per-target scores — to the run's own workspace (not a
temporary scratch location), with a provenance manifest, so the finding is
independently reproducible.

Three bins and a visible signal do not establish closure. Require resolution,
precision, stability, and controls appropriate to the exact claim. A localized
or proxy-based predictor may support a bounded predictive candidate; it still
requires independent-dataset replication before acceptance. A replicated
predictive finding does not establish a broader transfer or causal claim. When a control removes or reverses
the relationship, determine whether it reveals an artifact/nuisance relevant
to deployment or changes the comparison. Do not discard a surviving prospective
association merely because a different within-entity or stronger claim failed.
A proposed alternative driver is a new hypothesis, not an established cause.

Before abandoning a promising but noisy signal, check whether a feasible
expansion, finer resolution, or claim-aligned diagnostic can resolve it. Freeze
a power/precision target based on a meaningful effect and realistic pilot
uncertainty; an optimistic discovery estimate alone is insufficient. Add
balanced independent evidence under the planned confirmation or sequential
error-control rule. Do not keep sampling until a desired p-value appears. At
an actual data/resource ceiling, mark the claim inconclusive or blocked and
continue another feasible hypothesis. Limited power is not a scientific negative.

Use baselines to diagnose artifacts and classify model-specific or shared
degradation. The model need not perform worse than a baseline unless that
comparison is part of the frozen claim. Shared degradation can be valid, but
shared measurement artifacts cannot. Never turn a failed original criterion
into a pass by deleting it after observing the results.

Changing the comparison, metric, subgroup, direction, or required conjunction
after a failed or ambiguous test creates an outcome-informed hypothesis. Record
the original result, freeze the revised claim and testing plan, and confirm on
another unused independent dataset before certification. A repaired rerun of
the development dataset never substitutes for mandatory external replication.
Keep an exposure and testing history across hypothesis families and use a prespecified error-control strategy
for repeated confirmatory attempts; a repeatedly inspected holdout is discovery
evidence. If independent confirmation is unavailable, retain provisional status
and pursue other feasible work rather than certifying the discovery result.

Novelty is judged against the published record for this specific model: a
finding is novel when no prior work has shown this specific model failing in
this specific way. A published claim that a model class fails does not establish
that a specific newer model does; validating whether this model actually has the
failure is the contribution, and class-level prior work does not negate a
validated specific-model finding. Do not exclude or deprioritize a candidate
axis merely because prior work reports that failure for the model's class or for
other models; test it on this specific model. Confirming a class-attributed
failure on this model is a validated finding, and showing this model does not
have the class-attributed failure is also a finding. Model-specificity is not
required at all: a real, non-artifact degradation that a whole class of models
shares is a valid finding as long as no prior work reports this exact failure
for this exact model.

In broad generalizability mode, continue searching until at least one supported
axis has passed independent-dataset replication and all original completion
criteria, or a genuine stop applies. Save both development and replication SPCs,
the independence checks, frozen replication plan, actual test outputs, and all
attempts. A single-dataset positive, within-dataset holdout, corrected rerun, or
plan to replicate later cannot satisfy completion. Required external replication
cannot be labeled an optional extension. A valid negative closes its exact
hypothesis, not the whole audit.
Use accumulated successes and failures to propose scientifically distinct,
prospective hypotheses. If the current pool or features cannot test them,
construct or acquire suitable evidence within actual authorization. Completing
an initial list, using all released scores, or describing one costly experiment
does not establish exhaustion. Persist the ledger and queue across compaction.

Before a resource-limited stop, inspect the concrete remaining routes and
plausible cheaper alternatives. Unknown feasibility requires a bounded check
when one is possible. A hard stop must identify actual limits or observed
obstacles that leave no useful feasible authorized next action, including
alternative hypothesis discovery, panel construction, and confirmation. Do not
require disproving every imaginable experiment; do require examining the live
claims and credible routes already identified, and looking for another testable
axis when one is blocked. Honor explicit user/system limits and stop requests.

At a genuine stop, report honest negatives, unresolved claims, actions attempted,
and supported blockers. An incomplete search is not evidence the model has no
failure regime. Finish review must assess these requirements, execute available
next steps, and repeat before any final response.

## Sharing an audit over HTTPS

When the user asks to contribute an audit, read
[the submission guide](https://spectra.yashaektefaie.com/submit.md) and fetch
[the current submission format](https://spectra.yashaektefaie.com/api/submissions/schema).
Send the complete JSON bundle to `POST /api/submissions/validate`, resolve the
reported contract errors, then submit it to `POST /api/submissions`.
Submission creates a pending review record; it does not certify the scientific
claim or publish it. Save the returned submission ID and private receipt token
and use the returned status URL to check review status. Do not place that token
in a public artifact or a URL. Reading these instructions alone does not
request a submission.

Use a new, stable finding ID for each independent audit card. Cards can address
a new model, a new axis on an existing model, or independent evidence for an
already-audited axis. Preserve the exact checkpoint, task, frozen axis
definition, dataset, result, claim boundary, uncertainty, and provenance so
replication or disagreement remains distinguishable. Reference prior card IDs
when appropriate; never replace an existing card by reusing its ID.

Include the scored evidence and supporting artifact records required by the
current schema. Large scored tables, figures, and model outputs must be hosted
at stable HTTPS URLs and referenced with checksums, byte sizes, and row counts
where applicable. The submission interface accepts metadata and audit cards,
not bulk artifact uploads. If hosting or submission is unavailable, preserve
the complete bundle locally and report the blocker accurately.

Published cards can be discovered from
[the model directory](https://spectra.yashaektefaie.com/api/models). Follow its
links to models, axes, cards, and evidence. The registry is prior evidence, not
a substitute for the independence and confirmation requirements above. Keep
public claims bounded by the tested model version, task, dataset, and axis.
