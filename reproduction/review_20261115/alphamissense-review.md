# AlphaMissense individual notebook review

Reviewed all **34 entries individually**: primary 7, Codex r1/r2 5/4, Opus r1/r2 3/3, and Kimi r1/r2 6/6. The ledger records the dataset, axis construction, model scores, calculations, conclusions, limitations and changed Markdown cells for each entry.

This review read every prose and scientific code cell and the saved outputs. Shared functions were compared across related notebooks; related entries were not assumed identical. It did not rerun model inference, download every raw input, or recreate the original audit chronology. Notebook execution and a current reconstruction do not by themselves prove that the original discovery/confirmation sequence was prospective.

## Changes made

**33 Markdown cells in 21 notebooks** were revised; scientific code and saved output objects were checked against the pre-edit snapshot and left unchanged. Exact before/after text is in `alphamissense-markdown-changes.json`.

- The primary effective-depth endpoint comparison has **one paired assay**. Its zero-width bootstrap interval comes from resampling that one assay; it cannot measure uncertainty across assays. The lowest-depth group contains six terminal positions in one protein. The updated interpretation is descriptive and distinguishes this from a separate 61-assay occupancy comparison.
- Both Codex clinical junction analyses show a decline, but the target-minus-BLOSUM62 intervals include zero. Their confirmation data are gene-separated partitions of the same ClinVar release, not external cohorts. The DMS mechanism contrast also spans zero and is now described as inconclusive, without claiming absence of a mechanism.
- All six Opus entries explicitly describe absolute correlation and its loss of sign. The four local-property analyses now distinguish an automated directional label from a full protocol result and flag dependence among repeated assays of a protein. Both depth entries avoid treating 73 assays as 73 independent proteins. The current corrected cohort remains **273,135 variants**, while historical cohort metadata remains separately scoped.
- Kimi r1 entries 2–6 contained copied splice-distance wording despite computing entropy, terminal distance, length, ortholog breadth and allele frequency. Each description now matches its own code. The splice entry identifies its different GENCODE version and inclusion of terminal edges.
- The Kimi r1 allele-frequency result is marginal: the high-frequency group has only 40 pathogenic variants; its six-gene comparison is unresolved. Missing reported frequency is not zero population frequency.
- Kimi r2 pLDDT has a positive within-gene association, while the pooled interval spans zero and Grantham also changes. The prose does not claim a model-specific excess effect. The gene-level phyloP entry explains that an empty within-gene comparison is structurally expected for a gene-constant feature. CpG is described as categorical.
- Exact raw-MSA occupancy bin boundaries and live BioMart release dependence are stated where they affect interpretation or replay.

## Independent numerical checks

`verify_alphamissense_saved_outputs.py` completed **21 checks**:

- Endpoint subtraction for all predictors in all 12 Kimi notebooks, plus the six Kimi r2 paired-gene endpoint tables.
- All five whole-assay depth correlations in each Opus run recomputed from its 73 printed assay records; rounded source values reproduce the reported rho and p within tolerance.
- The Codex weighted-AUROC helper checked in 100 deterministic trials against scikit-learn, including ties and zero row weights.
- Exact equality handling at the Opus r2 occupancy boundaries.

All 34 notebooks were also inspected for saved error outputs; none were present. The check artifact identifies exactly which calculations were recomputed. This is not a claim that all scientific calculations or upstream inputs were independently rerun.

## Remaining evidence limits

Several entries are eligibility or feasibility records rather than performance tests. They are labeled accordingly in the ledger. Many positive associations are within a reused public cohort, and several comparator or within-gene intervals remain unresolved. Neither fact makes the notebook unusable; it limits the claim that can be made from it. The notebooks preserve their original code-generated labels and numerical outputs, with adjacent prose stating the narrower interpretation.

HTML rendering and browser layout checks are performed separately by the parent review. Presentation hashes and receipts must reflect the regenerated pages; this report does not claim those checks were performed by this reviewer.
