# SPECTRA discovery brief: STATE

Run a full SPECTRA generalizability audit of STATE from scratch. Begin by calling `get_spectra_protocol` and follow the returned protocol end to end. Work in discovery mode: do not read, query, or rely on any stored SPECTRA finding, run, provenance record, download record, or artifact. Do not call SPECTRA tools other than `get_spectra_protocol`. Use one persistent controller in this directory; do not delegate the audit to parallel agents.

Your goal is to discover and certify a real generalizability failure of STATE specifically: a prospective, frozen, quantified input-side axis along which performance degrades. Acquire and run the public code, data, model weights or official scored outputs, metadata, and model-independent references needed to finish the audit. A local-data, current-pool, compute, or scope ceiling is not a stopping condition when a concrete external resource can resolve it.

Apply the corrected closure gate exactly:

1. A fixed model-independent reference characterizes the result as model-specific or shared; it does not reject a real degradation merely because the reference also degrades.
2. A confound invalidates an axis only when the signal is actually a nuisance or measurement artifact. If analysis identifies the real driver, re-attribute it, freeze that driver as the new prospective axis, and confirm it.
3. Judge novelty by exact match for STATE: related class-level or other-model findings do not disqualify the result.
4. Rescue a small but directionally consistent non-artifactual effect before abandoning it: pre-declare a power-based sample target, expand the same frozen axis with balanced controls, and run its confirmatory test. If it remains inconclusive, follow the protocol's error-spending rule rather than repeatedly peeking.
5. A model-level negative is a last resort. Pursue every mechanistically plausible axis you flag using the external data or compute it requires, while ledgering genuine axis-level negatives honestly.

Run a fixed model-independent reference on the same perturbations, contexts, representation, and metric. Make an explicit gate call on whether STATE's degradation is larger, comparable, or smaller; retain a real shared degradation and label it accurately.

## Model-specific acquisition and discovery brief

- Acquire the released STATE checkpoint or official precomputed scored table, the exact official split definitions, perturbation/context metadata, and the raw labels needed for a same-task fixed reference. Keep target outcomes inaccessible until the prospective axis contract is frozen.
- The priority candidate is cross-cell-line generalization measured by transcriptomic distance of a held-out cell line from STATE's training panel. Acquire CCLE/DepMap expression profiles and at least one independent expression atlas; define the distance metric, genes, normalization, aggregation, levels, and direction before looking at STATE performance.
- Do not stop at the number of contexts available locally. Seek the external cell lines, perturbation families, annotations, or inference required to test the declared axis at the pre-calculated power ceiling.
- Treat true perturbation effect magnitude, number of differentially expressed genes, cell count, perturbation modality, dose/time, checkpoint family, and representation as required controls. If magnitude explains the curve, do not call magnitude itself distance from training; either re-attribute the claim or residualize/match it prospectively and confirm the actual distance axis.
- Use a transparent same-task reference such as transfer-the-training-context mean, identity/nearest-context transfer, or another frozen predictor justified before scoring. Do not use a reference that consumes held-out outcomes unavailable to STATE.

## Required outputs

Keep every script, manifest, frozen-axis specification, per-condition score, reference result, SPC table, plot, candidate-axis ledger, and report inside this directory. The final report must state the frozen axis, discovery/confirmation separation, power plan, level/context counts and measured ordering, spectral performance curve with uncertainty, same-example reference comparison, effect-size and cell-count controls, atlas replication, other confound checks, rejected candidates, exact-match novelty search, provenance and remaining gaps, and an explicit closure verdict. Do not submit anything to the SPECTRA pending queue.
