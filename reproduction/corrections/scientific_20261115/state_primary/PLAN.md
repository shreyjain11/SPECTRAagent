# STATE primary regression correction

Frozen before recalculation on 2026-11-15; prior revision: 1d3b45baa344751b4c34ea825479c0f39b09ec21.

Affected notebooks: state-featured/test-05, test-09, test-10 (shared regression implementation).

Keep the original cohort, support feature, standardized continuous covariates and two specifications (with and without observed DE-count adjustment). Use context and representation indicators; remove only the redundant subset indicators. Require a full-rank design. Canonical gene is the clustering unit across repeated contexts and representations. Use a finite-sample-corrected cluster sandwich covariance and t intervals with G-1 degrees of freedom. Report N, G, design rank, reference categories and any exclusions. Missing DE values will not be imputed as zero. No covariate or threshold will be selected based on the corrected result.

The adjusted-association conclusion must use the corrected interval, rather than the coefficient sign alone. Report the two specifications explicitly. This is a conditional association in the observed contexts, not a causal effect or confirmation in new patients/sites. The existing upstream cohort/axis and unrelated endpoint analyses will remain unchanged. Full notebooks will be rerun from the pinned cached source inputs if available.

Independent checks will compare estimates/fitted values with the old redundant design and compare clustered covariance with statsmodels. Duplicating each gene's records must not produce an artificial gain in nominal independent sample size.

Before recalculating the seven ontology checks, source inspection also identified the same regression defect in tests 13–19. Apply the identical specification correction there, preserving each ontology's original few-shot cohort, feature and covariates. Their endpoint curves are separate descriptive calculations; the adjusted coefficient will now include gene-clustered uncertainty. This expansion is based on duplicated faulty code, not on any newly calculated outcome.
