# Reporting adjustment after independent code review

Removed pooled-row Spearman p values from exploratory fixed-N, protocol, response-strength, density-trimming and gene-half summaries because repeated genes across contexts do not satisfy independent-row inference. Those summaries retain descriptive correlations and sample counts. Per-context and gene-aggregate tests remain separate. This changes reporting, not the frozen bootstrap estimators, seed, cohorts or contrasts in PLAN.md. All affected cells are reexecuted.
