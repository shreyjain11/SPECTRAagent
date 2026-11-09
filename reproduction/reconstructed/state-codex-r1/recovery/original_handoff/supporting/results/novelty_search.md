# Exact-match novelty search

Search date: 2026-07-17 UTC. Novelty rule: an exact match must concern **STATE itself**, the same Tahoe zero-shot held-out contexts, and the same quantified input-side axis/performance relationship. Related findings for a model class, another model, or another task are not disqualifying.

## Queries executed

- `"ST-SE-Tahoe" "S_score" generalization`
- `STATE single-cell perturbation model "S-phase" heterogeneity performance`
- `STATE Tahoe-100M cell cycle heterogeneity generalization RMSE`
- `site:biorxiv.org STATE Tahoe-100M generalization cell line cell cycle`
- `STATE single-cell perturbation model official paper Tahoe-100M`
- `Tahoe-100M official paper cell line held out STATE`
- `site:openreview.net STATE "Tahoe-100M"`
- `site:github.com arcinstitute STATE Tahoe model`

## Sources checked and exact-match assessment

| Source | Scope found | Exact match? |
|---|---|---|
| [STATE official repository](https://github.com/ArcInstitute/state) | Code, ST/SE descriptions, training and prediction workflows | No quantified S-score-heterogeneity or training-lineage-scarcity degradation |
| [STATE paper](https://openreview.net/pdf?id=QOMkmXVyiv) | STATE architecture, context-generalization benchmarks, aggregate baselines, and claims about modeling residual heterogeneity | No condition-level LFC-RMSE curve along either audited axis |
| [Tahoe-100M paper](https://www.biorxiv.org/content/10.1101/2025.02.20.639398v1) | Dataset construction: roughly 100M cells, 1,100 perturbations, 50 cancer cell lines | No STATE-specific generalizability audit along either axis |
| [PrePR-CT](https://doi.org/10.1038/s42256-026-01202-2) | Another model; analyzes effect strength and training/test transcriptomic similarity | Related class-level concept only, not STATE and not the same metric/split |
| [OCOO-T](https://www.biorxiv.org/content/10.64898/2026.06.08.731000v1.full) | Tahoe benchmark comparison using STATE evaluation tooling | Aggregate model comparison, not the audited axes |
| [On the role of drug representations](https://openreview.net/forum?id=Htzu1KrgwW) | Tahoe unseen-cell-line generalization and drug representations | Different predictor question and no exact audited axis |

Search results also included general cell-cycle/S-phase heterogeneity work and other perturbation-response models. None evaluated STATE on the same five held-out Tahoe contexts using baseline untreated-cell `S_score` sample SD, training-lineage scarcity, the same per-condition full-feature log-fold-change RMSE, and the same compound-blocked confirmation design.

## Verdict

No exact match found for either the frozen S-phase candidate or the lineage-scarcity follow-up. This satisfies the exact-match novelty check but does **not** rescue either candidate’s failed closure gate.
