# Independent data-quality audit

## Scope and method

Read the two supplied CSVs and dictionary without modifying them. Inspected raw strings before numeric parsing, blank tokens, inferred types, numeric minima/maxima, fractional values, negative values and common sentinel candidates. Tested unique/nonmissing join keys, duplicate rows, outer-merge coverage, dictionary ranges, cohort/arm missingness and cross-field consistency. Saved every issue with applicant ID, original values and proposed handling in `record_level_issues.csv`; retained all applicants and raw fields in `all_applicants_with_audit_flags.csv`.

Both survey files contain 1,618 unique applicants with no duplicate or missing IDs, no duplicate rows, and complete one-to-one matching. The data have blank-cell missingness; no nonblank numeric missing-value tokens or common sentinel candidates were found. Documented binary and bounded categorical variables are within range. No ID-based evidence of respondent attrition appears in the supplied extracts; item missingness remains. This does not establish that the extracts include all applicants in the original administrative population.

The dictionary calls the follow-up month `interview_month`, whereas the data call it `survey_month`. The actual column contains integers 1–12; use the actual column name and record the dictionary discrepancy. Neither survey year nor exact interview/application dates are supplied.

## Ages: substantive timing discrepancy

Baseline age is missing for 64 applicants and survey age for 6 (one overlap), leaving 1,549 comparable pairs and 69 unassessable pairs. Of observed pairs, 350 (22.6%) differ by an amount outside 2–4 years, a diagnostic tolerance around the approximate three-year description. This cutoff identifies a concern; it is not proof those 350 records are erroneous. Eleven ages decline and 86 remain unchanged.

| cohort | n | selected | age_pair_observed | age_gap_mean | age_gap_median | age_gap_min | age_gap_max | neighborhood_observed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A_2020 | 1176 | 593 | 1117 | 2.404655326768129 | 2.0 | -5.0 | 5.0 | 897 |
| A_2022 | 277 | 146 | 271 | 0.6642066420664207 | 1.0 | -4.0 | 4.0 | 0 |
| B_2018 | 165 | 91 | 161 | 4.490683229813665 | 5.0 | 2.0 | 7.0 | 0 |

The differences are systematically cohort-dependent: A2020 mostly +2/+3, A2022 mostly +0/+1, B2018 mostly +4/+5. Application year plus age difference equals 2022 or 2023 for 1,477 of 1,549 comparable records (95.4%). This pattern is compatible with a common follow-up period, but ages do not identify exact survey dates and this is an inference, not a correction. It is inconsistent with treating every cohort's follow-up as an identical three-year exposure window. Clarify the timing with the data provider; report cohort-specific results and avoid a uniform three-year causal interpretation.

The 11 definitely inconsistent chronological age pairs are:

| applicant_id | cohort | selected | age_at_application | age_at_survey | age_gap |
| --- | --- | --- | --- | --- | --- |
| 100044 | A_2022 | 0 | 15.0 | 13.0 | -2.0 |
| 100133 | A_2022 | 1 | 13.0 | 12.0 | -1.0 |
| 100368 | A_2020 | 0 | 15.0 | 10.0 | -5.0 |
| 100628 | A_2022 | 1 | 14.0 | 11.0 | -3.0 |
| 100849 | A_2022 | 0 | 12.0 | 10.0 | -2.0 |
| 100910 | A_2022 | 1 | 17.0 | 13.0 | -4.0 |
| 101003 | A_2022 | 0 | 14.0 | 13.0 | -1.0 |
| 101026 | A_2022 | 1 | 14.0 | 13.0 | -1.0 |
| 101503 | A_2022 | 1 | 15.0 | 14.0 | -1.0 |
| 101508 | A_2022 | 1 | 14.0 | 13.0 | -1.0 |
| 101532 | A_2022 | 0 | 13.0 | 12.0 | -1.0 |

Recommended treatment: preserve both original reports and issue flags; never overwrite age by adding/subtracting three. Retain applicants' valid outcomes. Baseline age may be an optional pretreatment covariate, with explicit missing indicator; follow-up age should not be a main control. An age-flag exclusion can be a sensitivity analysis but risks discarding nearly the entire recent cohort and is not a preferred primary sample definition. Cohort fixed effects address baseline level differences, not unequal follow-up duration or validity of suspect age values.

## Grade measurement conflicts

Fourteen applicants have highest-grade and completion-indicator conflicts (9 selected and 5 not selected). For all 14, all three completion flags equal zero despite highest grade at least 6. Thirteen conflict for grades 6, 7 and 8; ID 100734 conflicts only for grade 6. No completion flags violate nesting and no repetition-count variables disagree with their corresponding binary measures.

| applicant_id | cohort | selected | highest_grade | finished_g6 | finished_g7 | finished_g8 |
| --- | --- | --- | --- | --- | --- | --- |
| 100088 | B_2018 | 1 | 9 | 0.0 | 0.0 | 0.0 |
| 100203 | A_2020 | 1 | 11 | 0.0 | 0.0 | 0.0 |
| 100411 | B_2018 | 0 | 11 | 0.0 | 0.0 | 0.0 |
| 100466 | A_2020 | 0 | 8 | 0.0 | 0.0 | 0.0 |
| 100606 | B_2018 | 1 | 11 | 0.0 | 0.0 | 0.0 |
| 100704 | A_2020 | 1 | 11 | 0.0 | 0.0 | 0.0 |
| 100709 | B_2018 | 0 | 11 | 0.0 | 0.0 | 0.0 |
| 100734 | A_2022 | 1 | 6 | 0.0 | 0.0 | 0.0 |
| 100736 | A_2020 | 1 | 11 | 0.0 | 0.0 | 0.0 |
| 100769 | A_2020 | 0 | 11 | 0.0 | 0.0 | 0.0 |
| 100823 | B_2018 | 1 | 8 | 0.0 | 0.0 | 0.0 |
| 100831 | A_2020 | 1 | 8 | 0.0 | 0.0 | 0.0 |
| 101173 | B_2018 | 1 | 10 | 0.0 | 0.0 | 0.0 |
| 101591 | A_2020 | 0 | 10 | 0.0 | 0.0 | 0.0 |

The correct measurement is unknowable from the supplied fields. Preserve reported primary highest grade, flag these records and compare results excluding them; alternatively present a clearly labeled clean-grade analysis with contradictory measurements marked missing and raw-grade sensitivity. Do not silently recode all flags from highest grade or vice versa. Missing completion flags alone are not contradictions.

## Parent-age and work inconsistencies

Five parents are reported as no older than the applicant:

| applicant_id | age_at_survey | mother_age | father_age |
| --- | --- | --- | --- |
| 100389 | 14.0 | 14.0 | 39.0 |
| 100421 | 13.0 | 8.0 | 36.0 |
| 100659 | 16.0 | 32.0 | 1.0 |
| 100840 | 15.0 | 15.0 | 37.0 |
| 101329 | 16.0 | 16.0 | 37.0 |

In `parent_age_clean_derivative.csv` only those five impossible parent-age cells are set to missing, with originals retained. Two additional low but positive parent-child gaps are flagged for review: ID 100614 has mother age 26 and applicant age 15 (gap 11); ID 101047 has father age 19 and applicant age 15 (gap 4). Three gaps above 60 are flagged as unusual (not automatically corrected). Parents' survey-reported characteristics are unnecessary for the primary lottery comparison.

ID 100767 reports working=0 but hours_worked=4. Preserve both reports and check work-related results with this one record excluded. Thirty-two applicants report working=1 with zero weekly hours; temporary absence or different reference windows could explain this, so retain these zeros and disclose them. No positive private-enrollment responses coexist with explicit nonenrollment.

## Missingness and duration

Neighborhood is observed for 897 A2020 applicants, missing for 279 A2020 applicants, and absent for all 277 A2022 and 165 B2018 applicants. The missingness is therefore strongly cohort-patterned; do not use complete-case neighborhood adjustment on the full sample. Baseline socioeconomic stratum is missing in 279 records, parental schooling/income much more often than core outcomes. Treat missing values as missing, not zero; outcome-specific analyses should report the observed N and missingness by lottery arm. Pre-treatment covariate imputation, if used only for precision, should be outcome-blind and paired with missingness indicators. Do not impute missing outcomes as nonenrollment or no repetition.

Core outcome item missingness: enrollment 11, private attendance 18, highest grade 0, ever repeated 8 and total repetitions 8. All missingness by cohort and selection arm is in `missingness_by_cohort_arm.csv`. No applicant is dropped wholesale merely for a missing covariate.

There are 176 records with `years_in_school` 5 or 6, unusually long under a uniform approximately three-year reading. Many respondents' reported completed years also exceed the change in reported age. Given the broader timing ambiguity and uncertain school-year counting convention, retain and flag; prioritize direct highest grade and repetition outcomes, and do not impose a guessed duration cap.

## Nonzero diagnostic counts

| issue | n | certainty |
| --- | --- | --- |
| age_pair_missing | 69 | missing |
| age_decreases | 11 | contradiction |
| age_unchanged | 86 | review |
| age_gap_outside_2_4 | 350 | review |
| grade_6_contradiction | 14 | contradiction |
| grade_7_contradiction | 13 | contradiction |
| grade_8_contradiction | 13 | contradiction |
| any_grade_contradiction | 14 | contradiction |
| mother_not_older_than_child | 4 | contradiction |
| mother_age_gap_under_12 | 1 | review |
| mother_age_gap_over_60 | 1 | review |
| father_not_older_than_child | 1 | contradiction |
| father_age_gap_under_12 | 1 | review |
| father_age_gap_over_60 | 2 | review |
| nonworker_positive_hours | 1 | contradiction |
| worker_zero_hours | 32 | review |
| years_in_school_above_4 | 176 | review |

Counts overlap. A flag marks a review concern or known cross-field contradiction, not automatically an applicant to remove. This audit makes no outcome corrections except the explicitly identified parent-age derivative.
