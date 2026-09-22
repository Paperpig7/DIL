# Verification of the authoritative R analysis

Reviewed `code/run_analysis.R` and the generated tables. Independently rebuilt the core regressions and contrasts with NumPy using a separate least-squares implementation.

**Result: all 70 numerical comparisons passed, with maximum absolute discrepancy 3.75 × 10⁻¹⁴. No material statistical calculation errors found.** Exact comparisons are in `root_numerical_verification.csv`; rerun with `verify_root.py` in this directory.

## What was independently verified

- Four main point estimates and HC2 standard errors.
- Eight sex-specific effects and four direct boys-minus-girls contrasts, including all corresponding standard errors.
- All four baseline-adjusted estimates and standard errors, using cohort-mean imputation, full-baseline cohort centering, common baseline slopes across cohorts within assignment arms, and assignment interactions.
- HC3 standard errors; exclusions of the eleven declining-age records and fourteen grade-conflict records.
- Worst-case item-missingness identification bounds.

The primary estimates match the independent saturated cohort-by-assignment analysis to numerical precision. The R code's intervals/p-values differ slightly from the earlier independent tables because R uses a t reference distribution with residual degrees of freedom while the initial Python pass used a normal reference. This is expected and does not change conclusions.

## Methods assessment

The fixed full-baseline cohort shares are correctly retained when outcomes have item missingness. Cohort-specific treatment coefficients correctly avoid the unintended weighting of a common-coefficient fixed-effects regression. The latter is appropriately retained as a sensitivity check.

HC2 is implemented correctly. For the main saturated model it equals the sum of independent within-cell sample-variance contributions. The t reference distribution with df = n − rank is a conventional large-sample approximation for robust regression; it should not be described as an exact randomization test. With these samples, the difference from normal critical values is minor. Applicant-level uncertainty matches the stated applicant lottery; three-cluster inference would not be appropriate.

The adjusted model is correctly centered using full-cohort baseline covariate means, rather than response-sample or treatment-arm means. The treatment-interacted slopes allow the baseline-outcome relationship to vary across assignment groups; common slopes across cohorts are a modeling choice, and the specification is properly presented as sensitivity rather than replacing the design-based primary result. Baseline missingness indicators and imputation preserve applicants. No post-assignment survey characteristics enter those controls.

Sex contrasts correctly use the same cohort mix for boys and girls. The difference is tested directly from a saturated cell model, with the correct covariance. Main sex-interaction p-values exceed .05; differences in subgroup significance do not imply differences between sexes.

The missing-outcome bounds correctly retain each full cohort-by-assignment denominator and assign missing observations to the relevant lower/upper support. The interpretation as identification bounds rather than confidence intervals is essential. They do not eliminate sampling uncertainty or demonstrate a statistically significant enrollment effect.

Exclusions based on data inconsistencies can select applicants using a post-assignment report. They are correctly confined to sensitivity analysis. A2020-only estimates target another applicant population and cannot identify why effects differ across the three cohorts.

## Reporting corrections and deliverable checks

1. The joint baseline balance test is p = .017 (F = 2.585, 6 and 1609 df). Do not claim all groups were empirically balanced. Report the detected age/phone/missingness differences, retain the stated randomized design, and show that baseline adjustment preserves the main private-attendance/progression conclusions. The adjusted overall-enrollment estimate is −0.022 percentage points, close to zero.
2. Resolved after review: the original `analysis_data.csv` write preceded preparation of the adjustment controls. The final R pipeline now also saves `data/derived/adjusted_analysis_data.csv`, including the missing indicators, imputed controls, and centered covariates. This change does not affect estimates.
3. Keep the total-repetitions unit explicit as a count of repeated grades (or grade repetitions). Its effect of −0.055 is not a −5.5 percentage-point probability effect.
4. Describe the four outcomes as the main analysis family, without suggesting a prespecified analysis plan unless the exam actually supplies one.

The raw-data domain checks find no invalid binary/count-domain values; therefore the present use of original valid outcome columns rather than their identical `_clean` copies does not change estimates. Missingness and raw contradictions are transparently retained and audited.
