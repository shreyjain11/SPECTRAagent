# Exact-match novelty search

Search date: 2026-07-15 UTC. The search target was an exact match for the
released STATE model/checkpoint and the frozen input-side candidate axis—not
merely another virtual-cell model, a class-wide benchmark, or a broad
claim that cellular context matters.

Queries included:

- `STATE virtual cell model expected perturbation effect magnitude performance low signal perturbation`
- `STATE perturbation magnitude virtual cell`
- `State effect magnitude Tahoe-100M model performance`
- `ST-HVG-Tahoe benchmark performance dose magnitude`
- `ST-HVG-Tahoe weak perturbation`
- the full STATE paper title combined with `dose`, `effect size`, and
  `performance`

Primary sources checked:

- STATE paper/preprint: <https://www.biorxiv.org/content/10.1101/2025.06.26.661135v1>
- STATE NeurIPS record: <https://nips.cc/virtual/2025/loc/san-diego/129565>
- Released model collection: <https://huggingface.co/collections/arcinstitute/state>
- *Benchmarking virtual cell models for in-the-wild perturbation response*:
  <https://arxiv.org/abs/2604.27646>
- *SCALE*: <https://arxiv.org/abs/2603.17380>
- *OCOO-T*: <https://www.biorxiv.org/content/10.64898/2026.06.08.731000v1.full>
- *TxPert*: <https://doi.org/10.1038/s41587-026-03113-4>

The 2026 in-the-wild benchmark is the closest adjacent result: it reports
context-dependent performance and marked drops under stricter distribution
shifts. TxPert and related work also show that systematic perturbation effects
can make mean baselines strong. Neither source, as indexed and checked here,
reports this audit's exact frozen STATE checkpoint × input-side axis ×
same-example fixed-reference result. Accordingly, any novelty statement in the
report is limited to "no exact match found in this search"; it is not a claim
that the broad phenomenon or mechanism is unprecedented.
## 2026-07-16 exact-match update: certified A10 dose axis

Queries included `STATE Tahoe model low dose performance 0.05 5.0
generalization`, `"ST-HVG-Tahoe" dose performance`, and `"STATE" "Tahoe"
"0.05" "generalization"`. The STATE paper illustrates an individual 0.05 uM
condition, and adjacent drug-response work discusses dose-response mappings,
but the search found no exact match for the released ST-HVG-Tahoe zero-shot
checkpoint, balanced 199-drug three-dose axis, drug-block interval, nDE/cell
controls, and same-example fixed reference. Novelty is therefore retained as a
bounded exact-match result, not a claim that low-dose difficulty is broadly
unknown.
