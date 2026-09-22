# Current results: A2020 primary

For only the results displayed in the current slides, use `slide_regressions/` and the annotated `code/slide_regressions.md`. The 17 focused CSVs reproduce the displayed specifications, descriptive evidence and supporting sample/coding counts directly from raw data. They are the source for the current 24-slide deck and its detailed companion report. The broader tables below remain available for the earlier comprehensive report.

Use `slide_regressions/` for the current presentation, including the added age groups and categorical fixed-effects models. Use `tables/revised_*` for the earlier comprehensive analysis. A2020 is primary; A2022 and B2018 are separate checks. Earlier unprefixed model tables preserve the supplementary pooled analysis. Audit tables such as `variable_profile.csv` and `issue_summary.csv` still describe the full source data.

| Current table | Contents |
| --- | --- |
| `revised_policy_effects.csv` | Five offer effects, separately by cohort; ordinary 95% intervals, five-test Holm and nine-test sensitivity. |
| `revised_schooling_effects.csv` | Four retained schooling offer effects; four-test Holm and nine-test sensitivity. |
| `revised_first_stage.csv` | Offer effects on private attendance at G6, G7 and follow-up; current any-aid is a descriptive additional row. |
| `revised_iv_effects.csv` | Current-private-school IV effects on five outcomes, separately by cohort and baseline adjustment. |
| `revised_iv_entry_sensitivity.csv` | IV using G6/G7 private entry, which changes the exposure and required assumptions. |
| `revised_transition_summary.csv` | Observed private-school exits, paired denominators, unknown statuses and current enrollment. |
| `revised_missingness.csv` | Missing/observed counts and assignment differences for all nine outcomes. |
| `revised_binary_missing_bounds.csv` | Logical worst-case missing-data bounds for A2020 binary outcomes; these are not confidence intervals. |
| `revised_policy_sensitivity.csv` | All nine A2020 outcomes under named exclusions, HC3 and assignment-interacted baseline adjustment. |
| `revised_sex_effects.csv` | A2020 girls, boys and direct effect-difference tests. |
| `revised_baseline_balance.csv` | Cohort-specific observed baseline differences. |
| `revised_balance_permutation.csv` | Preferred joint balance check: 9,999 fixed-count lottery relabelings, with Monte Carlo uncertainty. |
| `revised_balance_joint_test.csv` | Secondary HC2 Wald diagnostic. The A2022 result is unreliable with a tiny age-missing group that perfectly predicts nonselection; use the permutation check. |

Binary effect estimates in CSVs are proportions; multiply by 100 for percentage points. School years, grades, repetition counts and hours retain their own units. Reported hours cover all observed applicants, including zero-hour respondents; the analysis does not condition on post-offer employment.

For the main IV table, choose `exposure=in_private_now` and `baseline_adjusted=FALSE`. The `reduced_form`, `first_stage` and sample counts belong to the same complete outcome/exposure sample. Thus their ratio need not equal a ratio taken from the separate policy and overall first-stage tables.

`ar_type` identifies whether the approximate robust AR confidence set is bounded, disjoint, unbounded or not reported. A disjoint set accepts values outside the two numerical endpoints; do not plot it as a finite interval. `ar_p_zero` is the zero-effect AR-type p-value, and `holm_ar_p` corrects five such tests. Constant A2022 marriage/parenthood outcomes have no ordinary robust inference reported.

Observed exits are not identified defiers. The current ATT discussion defines private schooling as treatment uptake and lottery selection as the offer. Control private attendance establishes two-sided uptake, so the IV complier effect is not generally ATT for all private attenders. No separate ATT number is claimed. All schooling IV estimates remain conditional on unverified exclusion, monotonicity and exposure-definition assumptions.

## Added age-group and controlled results

- `slide_regressions/age_groups.csv`, `age_effects.csv` and `age_heterogeneity.csv`: A2020 application ages 10–11, 12–13 and 14–18; all nine outcomes and direct equality tests. The 56 missing baseline ages stay in the primary analysis. These groups do not identify actual grades. Youngest-group marriage/parenthood have no observed events; their individual and joint age inference is not reported.
- `slide_regressions/fe_itt.csv`: all nine A2020 offer coefficients controlling for baseline sex, phone, imputed baseline age and its missingness indicator, with separate SES and neighborhood categorical fixed effects. Missing categories retain applicants. Phone is constant and aliased. HC2/t inference uses model rank 26.
- `slide_regressions/fe_iv.csv`: five corresponding IV specifications with the same baseline controls and fixed effects in both equations, exact common outcome/private-status samples, joint-HC2 AR confidence sets and first-stage diagnostics.
- `slide_regressions/fe_category_counts.csv`: the categorical coding and arm counts underlying those fixed effects.

The controlled results remain supplementary. Their coefficients are not raw differences in observed arm means. Fixed effects do not imply clustered errors. All choices made during this revision are exploratory.

## Equation and discussion revision

The 24-slide deck prints model equations above regression tables. The counterfactual-credibility slide reuses the A2020 permutation balance check, cohort totals and observed/missing counts. The main girls/boys schooling slide reuses the four schooling rows and direct interaction tests in `sex.csv`; the appendix retains all nine outcomes. No additional regression specification was fitted for these discussion slides.

The ATT slide now uses current private attendance as treatment uptake. Its control/treatment uptake shares come from `first_stages.csv`. Current aid receipt is not the assignment instrument or this treatment definition; the obsolete `current_aid.csv` output has been removed from the focused results.
