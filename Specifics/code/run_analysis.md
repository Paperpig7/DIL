# Walkthrough of `run_analysis.R`

This document explains the complete DIL analysis script in execution order. Each section introduces a chunk of code, explains its purpose and important choices, and identifies its outputs. **Every line of the original R script is retained, unchanged, in the R blocks below.** The original executable file remains available alongside this Markdown file.

**Current scope:** A2020 applicants are the primary population. The five policy outcomes are years in school since allocation, marriage/cohabitation, parenthood, working and weekly hours; the four earlier schooling outcomes are retained. A2022 and B2018 are separate checks. Sections 33-41 produce these current `revised_*` tables, descriptive school exits, and exploratory schooling IV estimates. Sections 1-17 prepare the data and reusable estimators; sections 18-32 retain the earlier pooled analysis as supplementary material. References to “primary” inside those older code blocks describe that earlier scope.

The current analysis uses the lottery **offer**, not current aid receipt, as the randomized assignment. Data-quality flags, exclusions used for sensitivity checks, and original data are kept distinct. No observed school history identifies an individual defier, and actual subsidy-recipient ATT is not identified by these files.

## How to use this walkthrough

Read and, if desired, execute the R blocks in order. Later blocks use objects created earlier. This is a plain `.md` file, not a knitted `.Rmd` document, so viewing it does not run the code.

To reproduce the analysis with the original script, run the following from the extracted project folder:

```sh
Rscript code/run_analysis.R
```

Only base R is required. For interactive, chunk-by-chunk execution in a fresh R or RStudio session, first set the working directory to the project folder containing `data/`, `code/`, and `results/`. Paths named below are relative to that project folder. Running the code regenerates derived files, tables and charts; it does not write to `data/raw/`.

### Objects used throughout the script

| Object | What it contains |
| --- | --- |
| `b`, `f`, `dict` | Baseline data, follow-up data, and the supplied dictionary. |
| `d` | The merged applicant data, later expanded with audit flags and baseline adjustment variables. |
| `weights` | Each cohort's share of the complete baseline sample. |
| `issues`, `ledger` | The accumulating audit entries and the final record-level issue table. |
| `main` | Earlier supplementary pooled results for the four schooling outcomes. |
| `rev_all` | Current within-cohort policy and schooling ITT results; A2020 is primary. |
| `rev_iv` | Current and entry-private IV estimates, with matching samples and AR-type sets. |
| `sex_results` | Girls' effects, boys' effects, and the direct boys-minus-girls contrasts. |
| `dx` | A copy of the prepared data containing centered covariates for the adjusted sensitivity. |

## Contents

1. [Set up paths and output folders](#1-set-up-paths-and-output-folders)
2. [Read the three supplied files](#2-read-the-three-supplied-files)
3. [Validate IDs, merge records, and define lottery cohorts](#3-validate-ids-merge-records-and-define-lottery-cohorts)
4. [Create a variable inventory and a merge summary](#4-create-a-variable-inventory-and-a-merge-summary)
5. [Create the record-level issue log and register missing values](#5-create-the-record-level-issue-log-and-register-missing-values)
6. [Screen numeric fields for unusual values](#6-screen-numeric-fields-for-unusual-values)
7. [Check dictionary domains and create explicit clean copies](#7-check-dictionary-domains-and-create-explicit-clean-copies)
8. [Check the change in age between surveys](#8-check-the-change-in-age-between-surveys)
9. [Check grade attainment and school-year consistency](#9-check-grade-attainment-and-school-year-consistency)
10. [Check repetition and school-attendance consistency](#10-check-repetition-and-school-attendance-consistency)
11. [Check parent ages against the applicant age](#11-check-parent-ages-against-the-applicant-age)
12. [Check employment against weekly hours](#12-check-employment-against-weekly-hours)
13. [Check whether reported school duration needs review](#13-check-whether-reported-school-duration-needs-review)
14. [Save the audit trail and first analysis dataset](#14-save-the-audit-trail-and-first-analysis-dataset)
15. [Define ordinary least squares with robust standard errors](#15-define-ordinary-least-squares-with-robust-standard-errors)
16. [Define how to estimate and test a weighted contrast](#16-define-how-to-estimate-and-test-a-weighted-contrast)
17. [Define the cohort-weighted lottery-offer estimator](#17-define-the-cohort-weighted-lottery-offer-estimator)
18. [Estimate the four primary outcomes and adjust p-values](#18-estimate-the-four-primary-outcomes-and-adjust-p-values)
19. [Describe the cohorts and estimate effects within each one](#19-describe-the-cohorts-and-estimate-effects-within-each-one)
20. [Compare baseline characteristics between lottery arms](#20-compare-baseline-characteristics-between-lottery-arms)
21. [Prepare missing baseline covariates for adjustment](#21-prepare-missing-baseline-covariates-for-adjustment)
22. [Test baseline balance jointly](#22-test-baseline-balance-jointly)
23. [Test whether outcome missingness differs by assignment](#23-test-whether-outcome-missingness-differs-by-assignment)
24. [Estimate sex-specific effects and directly test their difference](#24-estimate-sex-specific-effects-and-directly-test-their-difference)
25. [Run sensitivity analyses and save all adjustment variables](#25-run-sensitivity-analyses-and-save-all-adjustment-variables)
26. [Bound the effect under worst-case missing outcomes](#26-bound-the-effect-under-worst-case-missing-outcomes)
27. [Explore secondary outcomes and the work inconsistency](#27-explore-secondary-outcomes-and-the-work-inconsistency)
28. [Describe follow-up administration and sample composition](#28-describe-follow-up-administration-and-sample-composition)
29. [Plot the four primary effects](#29-plot-the-four-primary-effects)
30. [Plot the age-change distribution by cohort](#30-plot-the-age-change-distribution-by-cohort)
31. [Plot effects for girls and boys](#31-plot-effects-for-girls-and-boys)
32. [Verify the calculations and record the completed run](#32-verify-the-calculations-and-record-the-completed-run)
33. [Set the current scope and estimate the five policy outcomes](#33-set-the-current-scope-and-estimate-the-five-policy-outcomes)
34. [Check balance and missing outcomes within each cohort](#34-check-balance-and-missing-outcomes-within-each-cohort)
35. [Test sensitivity to data issues, controls and missing binary outcomes](#35-test-sensitivity-to-data-issues-controls-and-missing-binary-outcomes)
36. [Compare effects for girls and boys in A2020](#36-compare-effects-for-girls-and-boys-in-a2020)
37. [Save observed private-school exits and all school histories](#37-save-observed-private-school-exits-and-all-school-histories)
38. [Measure the instrument first stage and describe current aid](#38-measure-the-instrument-first-stage-and-describe-current-aid)
39. [Construct confidence sets that allow weak instruments](#39-construct-confidence-sets-that-allow-weak-instruments)
40. [Estimate schooling IV effects on exactly matched samples](#40-estimate-schooling-iv-effects-on-exactly-matched-samples)
41. [Verify revised results and draw the A2020 policy chart](#41-verify-revised-results-and-draw-the-a2020-policy-chart)

## 1. Set up paths and output folders

*Original script lines 1-15.*

This chunk prepares the analysis environment. `stringsAsFactors = FALSE` keeps imported text as text, and `warn = 1` prints warnings as they occur. The script reads its own command-line location and moves up two folders to find the project root. If there is no `--file=` argument, as in an interactive R session, it uses the current working directory.

`out`, `fig`, and `derived` point to the folders for tables, charts, and prepared data. The loop creates those folders if necessary. `write_table()` is a small helper that saves a named CSV without an extra row-number column and represents missing values as empty cells. None of these commands changes a raw input file.

```r
#!/usr/bin/env Rscript
# DIL assessment. Requires only base R (tested with R 4.3.3).
# Run from any directory: Rscript /path/to/dil_assessment/code/run_analysis.R
# Originals are never modified. All transformations and exclusions are explicit.
# CURRENT SCOPE: A2020 is primary. The revised_* tables below are authoritative
# for that scope. Earlier pooled tables are retained as supplementary results.
options(stringsAsFactors = FALSE, warn = 1)
args <- commandArgs(trailingOnly = FALSE)
script <- sub("^--file=", "", args[grepl("^--file=", args)])
root <- if (length(script)) dirname(dirname(normalizePath(script))) else normalizePath(".")
out <- file.path(root, "results", "tables")
fig <- file.path(root, "results", "figures")
derived <- file.path(root, "data", "derived")
for (p in c(out, fig, derived)) dir.create(p, recursive = TRUE, showWarnings = FALSE)
write_table <- function(x, name) write.csv(x, file.path(out, paste0(name, ".csv")), row.names = FALSE, na = "")
```

## 2. Read the three supplied files

*Original script lines 16-18.*

`b` contains the baseline records, `f` contains the follow-up records, and `dict` contains the variable dictionary. Empty cells and the text `NA` become R's missing-value marker, `NA`. `check.names = FALSE` preserves the supplied column names.

At this point the two survey files are still separate. Reading them does not pair respondents or repair values. The next chunk validates the IDs before joining the records.

```r
b <- read.csv(file.path(root, "data/raw/study_baseline.csv"), na.strings = c("", "NA"), check.names = FALSE)
f <- read.csv(file.path(root, "data/raw/study_followup.csv"), na.strings = c("", "NA"), check.names = FALSE)
dict <- read.csv(file.path(root, "data/raw/data_dictionary.csv"), check.names = FALSE)
```

## 3. Validate IDs, merge records, and define lottery cohorts

*Original script lines 19-26.*

The `stopifnot()` statements are safeguards: the script stops if either file has missing or duplicate IDs, or if the two sets of IDs differ. It then merges the files by `applicant_id`, keeps the baseline rows, sorts by ID, and verifies that the join did not expand the baseline sample. These checks prevent accidental duplication or mismatching by row position.

The `cohort` factor identifies the three municipality-year lotteries. Its explicit levels also provide a consistent ordering for tables. `weights` stores each cohort's share of **all baseline applicants**. These shares are calculated before any outcome-specific omissions and determine the primary pooled estimand.

```r
stopifnot(!anyNA(b$applicant_id), !anyNA(f$applicant_id), !anyDuplicated(b$applicant_id), !anyDuplicated(f$applicant_id))
stopifnot(setequal(b$applicant_id, f$applicant_id))
d <- merge(b, f, by = "applicant_id", all.x = TRUE, sort = TRUE)
stopifnot(nrow(d) == nrow(b))
d$cohort <- factor(paste(d$municipality, d$application_year, sep = "_"), levels = c("A_2020", "A_2022", "B_2018"))
stopifnot(!anyNA(d$cohort))
weights <- prop.table(table(d$cohort))

```

## 4. Create a variable inventory and a merge summary

*Original script lines 27-40.*

`profile()` loops over every column in a loaded dataset and reports its row count, missing count, number of distinct observed values, and minimum and maximum. For text fields, minima and maxima are alphabetical rather than numerical. `lapply()` creates one small result per variable, and `do.call(rbind, ...)` stacks those results into a table.

The chunk also saves the merge checks and records the dictionary's `interview_month` versus the file's `survey_month` discrepancy. It retains the observed name and documents the proposed alias rather than silently renaming or inventing a survey year. The duplicate-ID entries are zero because the earlier assertions passed; `anyDuplicated()` itself returns a first-duplicate position, not a general duplicate count.

**Outputs:** `variable_profile.csv`, `merge_checks.csv`, and `schema_discrepancy.csv`.

```r
# Audit every source variable. Counts use applicants, not filled cells.
profile <- function(dat, file) do.call(rbind, lapply(names(dat), function(v) {
  x <- dat[[v]]; observed <- x[!is.na(x)]
  data.frame(file=file, variable=v, n=nrow(dat), missing=sum(is.na(x)), unique=length(unique(observed)),
    min=if(length(observed)) as.character(min(observed)) else NA,
    max=if(length(observed)) as.character(max(observed)) else NA)
}))
write_table(rbind(profile(b,"study_baseline.csv"), profile(f,"study_followup.csv")), "variable_profile")
write_table(data.frame(check=c("baseline_rows","followup_rows","matched_ids","baseline_duplicate_ids","followup_duplicate_ids","unmatched_baseline","unmatched_followup"),
  count=c(nrow(b),nrow(f),nrow(d),anyDuplicated(b$applicant_id),anyDuplicated(f$applicant_id),sum(!b$applicant_id%in%f$applicant_id),sum(!f$applicant_id%in%b$applicant_id))), "merge_checks")
schema <- data.frame(file="study_followup.csv", dictionary_variable="interview_month", actual_variable="survey_month",
  action="Retain observed column name survey_month. Interpret as interview month; require confirmation of alias. No dates or years inferred.")
write_table(schema,"schema_discrepancy")

```

## 5. Create the record-level issue log and register missing values

*Original script lines 41-55.*

`issues` is a list that will collect audit entries. `add_issue()` receives a logical condition, a variable name, a rule, a severity label, and an explanation of the action. For each affected applicant it stores the ID, cohort, lottery status, original value, and decision. A custom `value` argument can show several related fields when documenting a contradiction.

Inside the helper, `<<-` appends to the `issues` list outside the function. The loop then logs every missing source value. It leaves missing outcomes missing, identifies the separate plan for missing baseline age and SES, and notes why neighborhood is excluded from the primary controls. **Logging an issue does not itself change a value or remove a row.**

```r
# A long ledger links each rule to the original value and the exact action.
issues <- list()
add_issue <- function(mask, variable, rule, severity, action, value = NULL) {
  ids <- which(!is.na(mask) & mask)
  if (!length(ids)) return(invisible(NULL))
  if (is.null(value)) value <- as.character(d[[variable]])
  issues[[length(issues)+1]] <<- data.frame(applicant_id=d$applicant_id[ids], cohort=as.character(d$cohort[ids]),
    selected=d$selected[ids], variable=variable, raw_value=value[ids], rule=rule, severity=severity, action=action)
}
for (v in setdiff(names(d),"cohort")) {
  if (anyNA(d[[v]])) add_issue(is.na(d[[v]]), v, "source_missing", "missing",
    if(v %in% c("age_at_application","ses_stratum")) "Keep NA. Optional adjusted model uses cohort mean and a missing indicator."
    else if(v=="neighborhood") "Keep NA. Exclude from primary controls because coverage differs by cohort."
    else "Keep NA. Use available observations for the specific outcome; no outcome imputation in point estimates.")
}
```

## 6. Screen numeric fields for unusual values

*Original script lines 56-73.*

This screen examines every numeric source field for nonfinite values, fractional values, negative values, and familiar missing-code candidates such as `-99` or `999`. It records the affected observations and produces a count for each variable.

These are review screens. A fraction can be legitimate for some measurements, and a value that resembles a sentinel must not be recoded without a verified definition. In the supplied files, these screens found no such numeric candidates. This chunk operates on the loaded numeric data; it is distinct from the optional independent audit's inspection of raw text tokens.

**Output:** `numeric_source_checks.csv`, plus any applicable ledger entries.

```r
# Scan every numeric source field independently of dictionary domain checks.
# Fractional/negative values are review flags, not universal deletion rules:
# some numeric quantities could validly be fractional in a future data version.
source_numeric <- names(d)[vapply(d,is.numeric,logical(1))]
numeric_checks <- do.call(rbind,lapply(source_numeric,function(v) {
  x <- d[[v]]
  nonfinite <- !is.na(x)&!is.finite(x)
  fractional <- !is.na(x)&is.finite(x)&x!=floor(x)
  negative <- !is.na(x)&is.finite(x)&x<0
  sentinel <- !is.na(x)&x%in%c(-999,-99,-9,-1,99,999,9999)
  add_issue(nonfinite,v,"source_numeric_nonfinite","review","Retain source value pending variable-specific review; no silent recoding.")
  add_issue(fractional,v,"source_numeric_fractional","review","Retain source value pending variable-specific review; verify units and integer requirements.")
  add_issue(negative,v,"source_numeric_negative","review","Retain source value pending variable-specific review; verify coding and allowed range.")
  add_issue(sentinel,v,"source_numeric_sentinel_candidate","review","Retain unless the data dictionary confirms a missing-value code; never guess a recoding.")
  data.frame(variable=v,observed=sum(!is.na(x)),nonfinite=sum(nonfinite),fractional=sum(fractional),
    negative=sum(negative),sentinel_candidate=sum(sentinel))
}))
write_table(numeric_checks,"numeric_source_checks")
```

## 7. Check dictionary domains and create explicit clean copies

*Original script lines 74-89.*

The script constructs the list of binary variables from the dictionary and checks that observed values are either 0 or 1. It also checks the allowed integer ranges for SES, neighborhood, interview month, and repetition counts. `domain_bad` holds a separate logical flag for each checked field.

For each field, a new `_clean` column copies the original and replaces a documented-domain violation with `NA`. The original column remains intact. Invalid treatment or sex codes stop the script because those fields define the comparison groups.

**Important:** the later models explicitly use the original outcome column names. No documented-domain violations occur in the supplied data, so those outcomes equal their domain-clean copies. This code is not a promise that new invalid outcomes would automatically be excluded from future models: any new domain violations would require an explicit model-input decision.

**Output:** `domain_checks.csv`, clean-copy columns, and any domain-violation ledger entries.

```r
binary <- unique(c("selected","male","has_phone", dict$Variable[dict$Type=="0/1"]))
binary <- intersect(binary,names(d))
domain_bad <- list()
for(v in binary) domain_bad[[v]] <- !is.na(d[[v]]) & !d[[v]] %in% c(0,1)
for(v in c("ses_stratum","neighborhood","survey_month","repeats_g6","total_repeats")) {
  bounds <- switch(v, ses_stratum=c(1,6), neighborhood=c(1,19), survey_month=c(1,12), c(0,3))
  domain_bad[[v]] <- !is.na(d[[v]]) & (d[[v]]<bounds[1] | d[[v]]>bounds[2] | d[[v]]!=floor(d[[v]]))
}
for(v in names(domain_bad)) {
  add_issue(domain_bad[[v]],v,"outside_dictionary_domain","invalid","Set derived clean field to NA. Preserve original field.")
  d[[paste0(v,"_clean")]] <- d[[v]]
  d[[paste0(v,"_clean")]][domain_bad[[v]]] <- NA
}
stopifnot(!any(domain_bad$selected), !any(domain_bad$male))
write_table(data.frame(variable=names(domain_bad), outside_domain=vapply(domain_bad,sum,integer(1))),"domain_checks")

```

## 8. Check the change in age between surveys

*Original script lines 90-102.*

`age_change` subtracts application age from survey age. Separate flags identify missing age pairs, decreasing ages, unchanged ages, and changes outside a diagnostic two-to-four-year window. The `!is.na()` conditions ensure that an unknown age difference is not mistaken for an observed discrepancy.

The script preserves both original ages. It creates `age_at_survey_clean` and sets it missing for the 11 declining-age pairs. This means that the survey-age derivative is not considered usable for those pairs; it does **not** establish which original age was wrong. The 350 changes outside two to four years receive review entries and remain in the primary sample.

The tolerance is a screen around the approximate three-year description, not a correction rule. Systematic cohort differences may indicate different survey horizons. The code never reconstructs age as baseline age plus three.

```r
# Approximate three-year timing is a study description, not an exact correction rule.
d$age_change <- d$age_at_survey-d$age_at_application
d$age_unverifiable <- is.na(d$age_change)
d$age_decreased <- !is.na(d$age_change) & d$age_change<0
d$age_unchanged <- !is.na(d$age_change) & d$age_change==0
d$age_outside_2_to_4 <- !is.na(d$age_change) & (d$age_change<2 | d$age_change>4)
d$age_at_survey_clean <- d$age_at_survey
d$age_at_survey_clean[d$age_decreased] <- NA
ageval <- paste0("baseline=",d$age_at_application,"; followup=",d$age_at_survey,"; change=",d$age_change)
add_issue(d$age_decreased,"age_at_survey","age_decreased","inconsistent",
  "Followup age clean set to NA; retain baseline age and schooling outcomes. Cannot determine which source age is wrong. Exclusion sensitivity reported.",ageval)
add_issue(d$age_outside_2_to_4,"age_at_survey","age_change_outside_2_to_4_screen","review",
  "Retain recorded ages and outcomes. Screening rule only. Systematic cohort differences require survey-date clarification, not automatic correction.",ageval)
```

## 9. Check grade attainment and school-year consistency

*Original script lines 103-120.*

The first checks flag two unusual histories: highest grade below 5 despite the program's grade-6 entry description, and school years below `highest_grade - 5`. Both depend on an assumed entry history, so they are review flags with no automatic correction.

The loop then checks grades 6, 7, and 8. For each grade, it compares the recorded completion indicator with whether `highest_grade` reaches that threshold. It only compares observed pairs. `grade_conflict` becomes true if any threshold disagrees.

The supplied data contain 14 applicants with conflicting grade reports. Both reports are preserved because the files do not establish which is authoritative. The primary grade analysis uses reported `highest_grade`; a later sensitivity excludes the flagged applicants.

```r
d$grade_conflict <- FALSE
d$grade_below_5_review <- !is.na(d$highest_grade) & d$highest_grade < 5
add_issue(d$grade_below_5_review,"highest_grade","highest_grade_below_expected_entry_history","review",
  "Retain. Grade 6 entry ordinarily follows grade 5, but exact eligibility/history is unverified. Exclusion sensitivity reported; no guessed correction.",
  paste0("highest_grade=",d$highest_grade,"; started_g6_private=",d$started_g6_private,"; years_in_school=",d$years_in_school))
d$school_years_below_grade_progress_review <- !is.na(d$years_in_school) & !is.na(d$highest_grade) & d$years_in_school < d$highest_grade-5
add_issue(d$school_years_below_grade_progress_review,"years_in_school","school_years_below_grade_progress_assuming_grade5_entry","review",
  "Retain both fields. This screen assumes grade 5 completed at allocation. Missing baseline grade and uncertain counting convention prevent a verified correction.",
  paste0("highest_grade=",d$highest_grade,"; years_in_school=",d$years_in_school))
for(g in 6:8) {
  v <- paste0("finished_g",g)
  flag <- !is.na(d[[v]]) & !is.na(d$highest_grade) & (d[[v]] != as.integer(d$highest_grade>=g))
  d[[paste0(v,"_conflict")]] <- flag
  d$grade_conflict <- d$grade_conflict|flag
  add_issue(flag,v,"completion_flag_disagrees_with_highest_grade","inconsistent",
    "Retain both reports; no source is known authoritative. Main grade result uses reported highest_grade. Sensitivity excludes conflicted applicants.",
    paste0("highest_grade=",d$highest_grade,"; ",v,"=",d[[v]]))
}
```

## 10. Check repetition and school-attendance consistency

*Original script lines 121-128.*

A repetition inconsistency occurs if grade-6 repetitions exceed total repetitions, or if `ever_repeated` disagrees with whether total repetitions exceed zero. The attendance check identifies respondents who say they are in private school but also explicitly say they are not enrolled.

The checks require the relevant fields to be observed. Missing fields do not become zeros or contradictions. Any conflicts enter the ledger, while the original outcomes remain available for the primary analysis. These particular checks find no contradictions in the supplied files.

```r
d$repeats_conflict <- (!is.na(d$repeats_g6)&!is.na(d$total_repeats)&d$repeats_g6>d$total_repeats) |
  (!is.na(d$ever_repeated)&!is.na(d$total_repeats)&d$ever_repeated!=as.integer(d$total_repeats>0))
add_issue(d$repeats_conflict,"total_repeats","repetition_fields_disagree","inconsistent",
  "Retain reported primary total. Sensitivity excludes conflicting records.",
  paste0("g6=",d$repeats_g6,"; ever=",d$ever_repeated,"; total=",d$total_repeats))
d$private_school_conflict <- !is.na(d$in_private_now)&!is.na(d$in_school_now)&d$in_private_now==1&d$in_school_now==0
add_issue(d$private_school_conflict,"in_private_now","private_but_not_enrolled","inconsistent",
  "Retain source values and exclude conflicted records in outcome sensitivity.",paste0("private=",d$in_private_now,"; enrolled=",d$in_school_now))
```

## 11. Check parent ages against the applicant age

*Original script lines 129-145.*

The loop applies the same checks to mothers and fathers. It computes the parent-child age gap, flags gaps above 60, and identifies a parent age no greater than the applicant's survey age. It also screens gaps below 12 and parent ages above 80.

Only the five internally incompatible parent-age cells are set missing in the named parent-age derivatives. Large or unusually small positive gaps receive review flags without correction. Original parent ages and all applicants remain in the data. These comparisons depend on the reported child age, so they do not establish the true age of either person.

Parent ages are not controls in the treatment-effect models. Their cleaning therefore does not drive the primary estimates.

```r
for(parent in c("mother","father")) {
  v <- paste0(parent,"_age")
  d[[paste0(parent,"_child_age_gap")]] <- d[[v]]-d$age_at_survey
  wide_gap <- !is.na(d[[paste0(parent,"_child_age_gap")]]) & d[[paste0(parent,"_child_age_gap")]]>60
  d[[paste0(parent,"_age_gap_over_60")]] <- wide_gap
  impossible <- !is.na(d[[v]])&!is.na(d$age_at_survey)&d[[v]]<=d$age_at_survey
  unusual <- !is.na(d[[v]])&((!is.na(d$age_at_survey)&d[[v]]-d$age_at_survey<12)|d[[v]]>80)
  d[[paste0(v,"_clean")]] <- d[[v]]
  d[[paste0(v,"_clean")]][impossible] <- NA
  add_issue(impossible,v,"parent_not_older_than_child","inconsistent",
    "Set derived parent age to NA; retain raw value and applicant. Parent ages are excluded from treatment-effect controls.",paste0(v,"=",d[[v]],"; child_age=",d$age_at_survey))
  add_issue(unusual&!impossible,v,"parent_age_gap_below_12_or_age_above_80","review",
    "Flag without changing. Biological relation and age validity cannot be verified. Exclude all followup parent ages from controls.",paste0(v,"=",d[[v]],"; child_age=",d$age_at_survey))
  add_issue(wide_gap,v,"parent_child_age_gap_above_60","review",
    "Retain raw value. Large parent-child gap is unusual, not proof of an error; biological relation and exact age cannot be verified. Exclude followup parent ages from controls.",
    paste0(v,"=",d[[v]],"; child_age=",d$age_at_survey,"; gap=",d[[paste0(parent,"_child_age_gap")]]))
}
```

## 12. Check employment against weekly hours

*Original script lines 146-150.*

The first flag identifies a respondent reporting no work but positive hours. The second logs respondents reporting work but zero weekly hours. These patterns are treated differently: the first is an internal conflict, while the second may reflect temporary absence or differences in the reference period.

Both source fields remain unchanged. Applicant 100767 has the first conflict; 32 applicants have the second pattern. A later secondary-outcome check excludes the first conflict only. It does not convert the 32 zero-hour values to missing.

```r
d$work_hours_conflict <- !is.na(d$working)&!is.na(d$hours_worked)&d$working==0&d$hours_worked>0
add_issue(d$work_hours_conflict,"hours_worked","not_working_but_positive_hours","inconsistent",
  "Retain source fields. Show sensitivity excluding conflict for secondary work outcomes.",paste0("working=",d$working,"; hours=",d$hours_worked))
add_issue(!is.na(d$working)&!is.na(d$hours_worked)&d$working==1&d$hours_worked==0,"hours_worked","working_but_zero_weekly_hours","review",
  "Retain. Could reflect temporary absence or reference-period differences; do not assume zero means missing.")
```

## 13. Check whether reported school duration needs review

*Original script lines 151-161.*

These checks identify more than four completed school years since allocation, and school years exceeding the recorded age change plus one. The one-year allowance is a diagnostic convention, not an established feature of the questionnaire.

The ledger entries include school years, both ages, their difference, and highest grade so that another analyst can inspect the inconsistency. All values are retained because exact dates and the school-year counting convention are unavailable. The script neither caps school years nor deletes respondents for these duration screens.

```r
# Duration checks are diagnostic screens. Exact survey dates and the convention
# for counting school years are unavailable; do not cap years or delete people.
d$years_in_school_above_4 <- !is.na(d$years_in_school)&d$years_in_school>4
d$years_in_school_exceeds_age_gap_plus_1 <- !is.na(d$years_in_school)&!is.na(d$age_change)&
  d$years_in_school>d$age_change+1
school_year_values <- paste0("years_in_school=",d$years_in_school,"; baseline_age=",d$age_at_application,
  "; followup_age=",d$age_at_survey,"; age_change=",d$age_change,"; highest_grade=",d$highest_grade)
add_issue(d$years_in_school_above_4,"years_in_school","school_years_since_allocation_above_4","review",
  "Retain as a requested policy outcome with a timing/definition caveat. Five or six years conflict with a uniform three-year interpretation but may fit the older B2018 cohort. Clarify dates and counting convention; do not cap or infer a correction.",school_year_values)
add_issue(d$years_in_school_exceeds_age_gap_plus_1,"years_in_school","school_years_exceed_age_change_plus_1","review",
  "Retain. Completed school years exceed reported age change plus a one-year diagnostic allowance. Age errors, varying followup horizons or school-year counting could explain this; do not cap the value or delete the applicant.",school_year_values)
```

## 14. Save the audit trail and first analysis dataset

*Original script lines 162-174.*

`primary_logic_flag` combines the grade, repetition, and private-school/enrollment contradiction flags. It does not include every review flag, such as the sole grade-4 history or an unusual age change. In these data the combined flag identifies the same 14 grade-conflict applicants.

The accumulated issue entries are stacked, sorted, and saved. The summary counts distinct applicants within each rule and severity. An applicant can appear under several rules, so counts across rules should not be added into a total number of people to exclude.

The chunk also saves all applicants with original fields, clean derivatives and flags; the 419 missing or off-window age pairs; the 11 declining-age pairs; and the 14 primary schooling conflicts. This first dataset precedes the later preparation of adjustment covariates. A second dataset will include those covariates.

**Outputs:** `issue_ledger.csv`, `issue_summary.csv`, `analysis_data.csv`, `age_review_records.csv`, `age_decreased_records.csv`, and `schooling_conflict_records.csv`.

```r
d$primary_logic_flag <- d$grade_conflict|d$repeats_conflict|d$private_school_conflict
ledger <- do.call(rbind,issues)
ledger <- ledger[order(ledger$applicant_id,ledger$rule,ledger$variable),]
write.csv(ledger,file.path(derived,"issue_ledger.csv"),row.names=FALSE,na="")
summary_issue <- aggregate(applicant_id~rule+severity,ledger,function(x) length(unique(x)))
names(summary_issue)[3] <- "applicants"
write_table(summary_issue,"issue_summary")
write.csv(d,file.path(derived,"analysis_data.csv"),row.names=FALSE,na="")
agecols <- c("applicant_id","cohort","selected","male","age_at_application","age_at_survey","age_change","age_unverifiable","age_decreased","age_unchanged","age_outside_2_to_4","age_at_survey_clean")
write.csv(d[d$age_outside_2_to_4|d$age_unverifiable,agecols],file.path(derived,"age_review_records.csv"),row.names=FALSE,na="")
write.csv(d[d$age_decreased,agecols],file.path(derived,"age_decreased_records.csv"),row.names=FALSE,na="")
write.csv(d[d$primary_logic_flag,c("applicant_id","cohort","selected","highest_grade","finished_g6","finished_g7","finished_g8","total_repeats","repeats_g6","ever_repeated","in_private_now","in_school_now","grade_conflict","repeats_conflict","private_school_conflict")],file.path(derived,"schooling_conflict_records.csv"),row.names=FALSE,na="")

```

## 15. Define ordinary least squares with robust standard errors

*Original script lines 175-191.*

`robust_fit()` runs `lm()` to estimate ordinary least squares coefficients, obtains the design matrix `X`, and constructs a heteroskedasticity-robust covariance matrix. Redundant coefficients are removed before inverting the matrix used for that covariance calculation.

`bread` is `(X'X)^(-1)`. The vector `h` contains leverage values, which measure how unusual each observation's regressor combination is. The residuals are `e`. HC2 uses `e² / (1 - h)` and HC3 uses `e² / (1 - h)²`; `pmax()` protects the denominator against numerical division by zero. The surrounding matrix products convert these adjusted residual variances into coefficient uncertainty.

The function returns the fitted model, coefficients, covariance matrix, sample size, and residual degrees of freedom. HC2 and HC3 change standard errors, not the OLS point estimates. These are **applicant-level robust errors, not clustered errors**. For saturated assignment-cell means, HC2 equals the familiar sample-variance-over-sample-size formula.

```r
# Base R HC2/HC3 robust covariance. Individual applicants are lottery units.
# For saturated cell means HC2 exactly reproduces s^2/n for each cell.
robust_fit <- function(formula,data,hc="HC2") {
  fit <- lm(formula,data=data)
  X <- model.matrix(fit)
  if(fit$rank<ncol(X)) {
    keep <- !is.na(coef(fit)); X <- X[,keep,drop=FALSE]
  }
  bread <- solve(crossprod(X))
  h <- rowSums((X%*%bread)*X)
  e <- residuals(fit)
  power <- if(hc=="HC3") 2 else 1
  V <- bread%*%crossprod(X,X*as.numeric(e^2/pmax(1-h,1e-10)^power))%*%bread
  co <- coef(fit); co <- co[!is.na(co)]
  dimnames(V) <- list(names(co),names(co))
  list(fit=fit,coef=co,V=V,n=nrow(X),df=fit$df.residual)
}
```

## 16. Define how to estimate and test a weighted contrast

*Original script lines 192-198.*

A contrast is a weighted combination of regression coefficients. `L` specifies those weights. The helper first aligns them with the coefficient names, then computes the estimate `L' beta` and its standard error `sqrt(L' V L)`.

`qt(.975, df)` supplies the two-sided 95% Student t critical value. `pt()` supplies the two-sided p-value, using the model's residual degrees of freedom. The returned row contains the estimate, standard error, interval, p-value, model N and degrees of freedom. The zero-standard-error branch avoids an undefined division.

These t-reference intervals are approximate robust inference, not exact randomization intervals. Using the covariance matrix in the contrast is important: adding standard errors directly would be incorrect.

```r
contrast <- function(fit,L) {
  L <- L[names(fit$coef)]
  est <- sum(L*fit$coef); se <- sqrt(as.numeric(t(L)%*%fit$V%*%L))
  crit <- qt(.975,fit$df)
  data.frame(estimate=est,se=se,ci_low=est-crit*se,ci_high=est+crit*se,
    p_value=if(se>0) 2*pt(-abs(est/se),fit$df) else if(est==0) 1 else 0,n=fit$n,df=fit$df)
}
```

## 17. Define the cohort-weighted lottery-offer estimator

*Original script lines 199-216.*

`stratified()` is the central estimation helper. It first removes observations missing the particular outcome `y`. It then estimates separate cohort intercepts and separate cohort-by-selection effects. In R's formula, `0 + cohort` gives each cohort its own intercept, and `cohort:selected` gives each cohort its own offer effect. With just one retained cohort, it uses `Y ~ selected` instead.

The contrast weights average these within-cohort offer effects using the baseline cohort shares. The same shares also standardize the reported control and selected means. The helper returns those means and each arm's observed outcome N alongside the effect and uncertainty.

If the input deliberately contains only some cohorts, their target shares are renormalized to sum to one. This happens in the A2020-only check. An entire cohort absent because of missing outcomes would also be dropped and the remaining shares renormalized. In the primary supplied data, every cohort is represented for all four outcomes.

Fixed cohort shares avoid letting item nonresponse redefine the cohort mixture. They do not remove bias if observed respondents are unrepresentative within a cohort and treatment arm.

```r
# Fixed target weights use ALL randomized applicants, unchanged by item nonresponse.
# Estimate E[Y(1)-Y(0)] averaged over the baseline cohort shares.
stratified <- function(data,y,hc="HC2",target_weights=weights) {
  dat <- data[!is.na(data[[y]]),]
  dat$cohort <- droplevels(dat$cohort)
  W <- target_weights[levels(dat$cohort)]; W <- W/sum(W)
  fit <- robust_fit(as.formula(paste(y,if(nlevels(dat$cohort)>1) "~ 0 + cohort + cohort:selected" else "~ selected")),dat,hc)
  L <- setNames(rep(0,length(fit$coef)),names(fit$coef))
  if(nlevels(dat$cohort)>1) {
    for(s in names(W)) L[paste0("cohort",s,":selected")] <- W[s]
  } else L["selected"] <- 1
  r <- contrast(fit,L)
  r$control_mean <- sum(W*vapply(names(W),function(s) mean(dat[dat$cohort==s&dat$selected==0,y]),numeric(1)))
  r$selected_mean <- sum(W*vapply(names(W),function(s) mean(dat[dat$cohort==s&dat$selected==1,y]),numeric(1)))
  r$n_control <- sum(dat$selected==0); r$n_selected <- sum(dat$selected==1)
  r$outcome <- y
  r
}
```

## 18. Estimate the four primary outcomes and adjust p-values

*Original script lines 217-224.*

**Scope note: this chunk retains the earlier supplementary pooled analysis. The current A2020 primary tables begin in section 33.**

The primary outcomes are current enrollment, current private-school attendance, highest completed grade, and total repetitions. The loop applies `stratified()` to each original outcome column and stacks the four result rows.

`p.adjust(..., "holm")` adjusts the four primary p-values for multiple testing. The effect estimates, standard errors, and ordinary 95% intervals are not changed. Binary effects are stored as proportions in the CSV; multiply them by 100 when presenting percentage points. Highest grade is measured in grade levels, and `total_repeats` is a count of repetitions even though the script groups both under the label `grades`.

**Output:** `primary_effects.csv`.

```r
primary <- c("in_school_now","in_private_now","highest_grade","total_repeats")
labels <- c(in_school_now="Currently enrolled",in_private_now="Currently in private school",highest_grade="Highest grade completed",total_repeats="Total grade repetitions")
main <- do.call(rbind,lapply(primary,function(y) stratified(d,y)))
main$holm_p <- p.adjust(main$p_value,"holm")
main$label <- labels[main$outcome]
main$unit <- ifelse(main$outcome%in%c("in_school_now","in_private_now"),"proportion","grades")
write_table(main,"primary_effects")

```

## 19. Describe the cohorts and estimate effects within each one

*Original script lines 225-238.*

**Scope note: this chunk retains the earlier supplementary pooled analysis. The current A2020 primary tables begin in section 33.**

For each lottery cohort, this chunk saves the number of applicants, treatment and control counts, offer rate, baseline target weight, and age-comparison summary. It also tabulates the distribution of recorded age changes by cohort, including missing age differences.

The nested loops then estimate each primary outcome separately in each cohort. These results help show what the pooled estimate combines and are especially useful when survey timing appears to vary across cohorts. The code does not assume that cohort-specific effects all measure the same elapsed follow-up period.

**Outputs:** `cohort_summary.csv`, `age_change_distribution.csv`, and `cohort_effects.csv`.

```r
cohorts <- do.call(rbind,lapply(levels(d$cohort),function(s) {
  x <- d[d$cohort==s,]
  data.frame(cohort=s,n=nrow(x),selected=sum(x$selected),control=sum(x$selected==0),selected_share=mean(x$selected),target_weight=as.numeric(weights[s]),
    age_pairs=sum(!is.na(x$age_change)),mean_age_change=mean(x$age_change,na.rm=TRUE),median_age_change=median(x$age_change,na.rm=TRUE),
    age_decreased=sum(x$age_decreased),age_unchanged=sum(x$age_unchanged),age_outside_2_to_4=sum(x$age_outside_2_to_4),age_missing=sum(x$age_unverifiable))
}))
write_table(cohorts,"cohort_summary")
age_dist <- as.data.frame(table(cohort=d$cohort,age_change=d$age_change,useNA="ifany"))
write_table(age_dist,"age_change_distribution")
cohort_results <- do.call(rbind,lapply(levels(d$cohort),function(s) do.call(rbind,lapply(primary,function(y) {
  rr <- stratified(d[d$cohort==s,],y); rr$cohort <- s; rr
}))))
write_table(cohort_results,"cohort_effects")

```

## 20. Compare baseline characteristics between lottery arms

*Original script lines 239-248.*

**Scope note: this chunk retains the earlier supplementary pooled analysis. The current A2020 primary tables begin in section 33.**

The script creates indicators for missing baseline age, SES, and neighborhood. It then uses the cohort-weighted estimator to compare sex, age, phone access, SES, and those missingness indicators between selected and nonselected applicants.

For each variable, the standardized difference divides the cohort-weighted mean difference by `sqrt((control variance + selected variance) / 2)`. These variances pool observations across cohorts within each arm. This denominator is not a within-cohort standard deviation or a sample-size-weighted pooled variance.

The table describes observed baseline comparability. It cannot prove correct lottery implementation, and missing baseline values still require care. The actual neighborhood code is not an adjustment control later.

**Output:** `baseline_balance.csv`.

```r
# Balance diagnostics use exclusively information recorded before assignment.
for(v in c("age_at_application","ses_stratum","neighborhood")) d[[paste0(v,"_missing")]] <- as.integer(is.na(d[[v]]))
balance_vars <- c("male","age_at_application","has_phone","ses_stratum","age_at_application_missing","ses_stratum_missing","neighborhood_missing")
balance <- do.call(rbind,lapply(balance_vars,function(v) {
  rr <- stratified(d,v)
  # Raw pooled SD is reported explicitly, not confused with a hypothesis test.
  sd_pool <- sqrt((var(d[d$selected==0,v],na.rm=TRUE)+var(d[d$selected==1,v],na.rm=TRUE))/2)
  rr$standardized_difference <- rr$estimate/sd_pool; rr
}))
write_table(balance,"baseline_balance")
```

## 21. Prepare missing baseline covariates for adjustment

*Original script lines 249-257.*

**Scope note: this chunk retains the earlier supplementary pooled analysis. The current A2020 primary tables begin in section 33.**

For baseline age and SES, this chunk creates an `_imp` copy. Within each cohort, it fills missing entries in that copy with the mean of observed baseline values. If the cohort mean is unavailable, it falls back to the overall observed mean. The source columns remain unchanged.

The earlier missingness indicators allow the adjusted model to distinguish an imputed value from a genuinely observed value at the mean. Neither outcomes nor lottery assignment are used to choose the imputation values. This is a transparent preparation for covariate adjustment, not a claim that the filled value is the person's true age or SES. No outcome values are imputed.

```r
for(v in c("age_at_application","ses_stratum")) {
  d[[paste0(v,"_imp")]] <- d[[v]]
  for(s in levels(d$cohort)) {
    ids <- which(d$cohort==s)
    mu <- mean(d[[v]][ids],na.rm=TRUE)
    if(!is.finite(mu)) mu <- mean(d[[v]],na.rm=TRUE)
    d[[paste0(v,"_imp")]][ids[is.na(d[[v]][ids])]] <- mu
  }
}
```

## 22. Test baseline balance jointly

*Original script lines 258-264.*

**Scope note: this chunk retains the earlier supplementary pooled analysis. The current A2020 primary tables begin in section 33.**

`controls` contains six baseline variables: sex, phone status, imputed age, age missingness, imputed SES, and SES missingness. The model regresses lottery selection on cohort plus these covariates.

The robust Wald statistic tests whether the six covariate coefficients jointly equal zero after accounting for cohort. It uses their covariance matrix, divides by the number of restrictions `q`, and obtains an approximate F-reference p-value. Neighborhood is not part of this joint test.

For the supplied data, the joint p-value is about 0.017. This is evidence of detectable baseline differences, not an automatic diagnosis of why they occurred. It motivates reporting the adjustment sensitivity and qualifying the counterfactual's credibility.

**Output:** `balance_joint_test.csv`.

```r
controls <- c("male","has_phone","age_at_application_imp","age_at_application_missing","ses_stratum_imp","ses_stratum_missing")
balfit <- robust_fit(as.formula(paste("selected ~ cohort +",paste(controls,collapse=" + "))),d)
tested <- intersect(controls,names(balfit$coef))
q <- length(tested); beta <- balfit$coef[tested]; vv <- balfit$V[tested,tested]
stat <- as.numeric(t(beta)%*%solve(vv,beta))/q
write_table(data.frame(test="Joint baseline balance, conditional on cohort",F_statistic=stat,numerator_df=q,denominator_df=balfit$df,p_value=pf(stat,q,balfit$df,lower.tail=FALSE)),"balance_joint_test")

```

## 23. Test whether outcome missingness differs by assignment

*Original script lines 265-274.*

**Scope note: this chunk retains the earlier supplementary pooled analysis. The current A2020 primary tables begin in section 33.**

For every follow-up field except the ID, the script creates a temporary indicator equal to one when that field is missing. Treating this indicator as an outcome estimates the cohort-weighted difference in missingness between lottery arms. The table also records the raw count missing in each arm.

The second table reports missing counts for each primary outcome separately by cohort and assignment. These checks distinguish matching IDs from complete measurement: an applicant can be present in both files but lack one outcome. Similar missingness rates do not prove that missing outcomes are ignorable.

**Outputs:** `outcome_missingness.csv` and `primary_missingness_by_cohort.csv`.

```r
# Outcomes are not imputed for primary estimates. Missingness itself is an outcome.
missing <- do.call(rbind,lapply(setdiff(names(f),"applicant_id"),function(v) {
  xx <- d; xx$item_missing <- as.integer(is.na(xx[[v]])); rr <- stratified(xx,"item_missing")
  rr$outcome <- v; rr$missing_control <- sum(is.na(xx[[v]])&xx$selected==0); rr$missing_selected <- sum(is.na(xx[[v]])&xx$selected==1)
  rr
}))
write_table(missing,"outcome_missingness")
missing_cohort <- do.call(rbind,lapply(primary,function(v) do.call(rbind,lapply(split(d,list(d$cohort,d$selected),drop=TRUE),function(x) data.frame(outcome=v,cohort=as.character(x$cohort[1]),selected=x$selected[1],n=nrow(x),missing=sum(is.na(x[[v]])))))))
write_table(missing_cohort,"primary_missingness_by_cohort")

```

## 24. Estimate sex-specific effects and directly test their difference

*Original script lines 275-313.*

**Scope note: this chunk retains the earlier supplementary pooled analysis. The current A2020 primary tables begin in section 33.**

For each outcome, `group` identifies every cohort-by-sex-by-assignment combination. `Y ~ 0 + group` estimates a separate mean for each observed cell. The contrast for each sex subtracts its control mean from its selected mean within every cohort, then combines the differences using the same full-sample cohort shares.

`Ls[[2]] - Ls[[1]]` directly estimates the boys' effect minus the girls' effect. Standardizing both sexes to the same cohort mix helps distinguish a sex difference from a difference in cohort composition. The code also calculates that interaction separately within each cohort.

The Holm adjustment covers the four pooled boys-minus-girls p-values only. It does not adjust every sex-specific p-value. `n` is the sample size of the full fitted model, while `subgroup_n` records the relevant sex's observed sample size. The code assumes the required comparison cells are represented, as they are in these data.

A significant estimate for girls and an insignificant estimate for boys is not, by itself, evidence of different effects. The direct contrast answers that question.

**Outputs:** `sex_effects.csv` and `sex_interactions_by_cohort.csv`.

```r
# Saturate cohort x sex x assignment; compare boys and girls at the SAME cohort mix.
sex_effects <- list(); sex_by_cohort <- list()
for(y in primary) {
  dd <- d[!is.na(d[[y]]),]
  dd$group <- factor(paste(dd$cohort,dd$male,dd$selected,sep="__"))
  fit <- robust_fit(as.formula(paste(y,"~ 0 + group")),dd)
  Ls <- list()
  for(sex in 0:1) {
    L <- setNames(rep(0,length(fit$coef)),names(fit$coef))
    for(s in names(weights)) {
      L[paste0("group",s,"__",sex,"__1")] <- weights[s]
      L[paste0("group",s,"__",sex,"__0")] <- -weights[s]
    }
    Ls[[sex+1]] <- L
    rr <- contrast(fit,L); rr$outcome <- y; rr$sex <- if(sex==0) "Girls" else "Boys"
    rr$subgroup_n <- sum(dd$male==sex)
    rr$control_mean <- sum(weights*vapply(names(weights),function(s) mean(dd[dd$cohort==s&dd$male==sex&dd$selected==0,y]),numeric(1)))
    sex_effects[[length(sex_effects)+1]] <- rr
  }
  rr <- contrast(fit,Ls[[2]]-Ls[[1]]); rr$outcome <- y; rr$sex <- "Boys minus girls"; rr$subgroup_n <- nrow(dd); rr$control_mean <- NA
  sex_effects[[length(sex_effects)+1]] <- rr
  for(s in names(weights)) {
    L <- setNames(rep(0,length(fit$coef)),names(fit$coef))
    for(sex in 0:1) {
      sign <- if(sex==1) 1 else -1
      L[paste0("group",s,"__",sex,"__1")] <- sign
      L[paste0("group",s,"__",sex,"__0")] <- -sign
    }
    rr <- contrast(fit,L); rr$outcome <- y; rr$cohort <- s
    sex_by_cohort[[length(sex_by_cohort)+1]] <- rr
  }
}
sex_results <- do.call(rbind,sex_effects)
sex_results$holm_interaction_p <- NA_real_
is_diff <- sex_results$sex=="Boys minus girls"
sex_results$holm_interaction_p[is_diff] <- p.adjust(sex_results$p_value[is_diff],"holm")
write_table(sex_results,"sex_effects")
write_table(do.call(rbind,sex_by_cohort),"sex_interactions_by_cohort")

```

## 25. Run sensitivity analyses and save all adjustment variables

*Original script lines 314-349.*

**Scope note: this chunk retains the earlier supplementary pooled analysis. The current A2020 primary tables begin in section 33.**

This loop estimates several alternatives for every primary outcome. The exclusions are **separate checks, not cumulative cleaning steps**:

1. Replace HC2 with HC3 standard errors.
2. Exclude the 11 declining-age records.
3. Exclude the 14 primary schooling contradictions.
4. Exclude the sole highest-grade-below-5 review record.
5. Restrict to A2020, whose age changes are closest to the stated horizon.
6. Estimate ordinary cohort fixed effects with one common treatment coefficient. This implicitly weights cohort effects by observed cohort size times `p(1-p)`, rather than imposing the baseline target shares.
7. Add the six baseline covariates, centered at their full-cohort means, and interact each with selection. Cohort intercepts and treatment effects remain cohort-specific. Covariate slopes can differ between assignment arms but are common across cohorts. The final contrast still uses the baseline cohort shares.

`dx` retains all applicants and holds the centered covariates used for adjustment. Each fitted model handles only the observations missing its own outcome. Excluding records flagged using follow-up data can change the population being compared; these checks are not proof that the remaining data are correct.

**Outputs:** `sensitivity_effects.csv` and `adjusted_analysis_data.csv`. The latter adds the imputed values, missingness indicators, and centered controls to the earlier prepared data.

```r
# Robustness to specification, missingness, and questionable records.
sensitivity <- list()
add_sensitivity <- function(result,label) {result$specification <- label; sensitivity[[length(sensitivity)+1]] <<- result}
for(y in primary) {
  add_sensitivity(stratified(d,y,"HC3"),"Primary point estimate, HC3 standard errors")
  add_sensitivity(stratified(d[!d$age_decreased,],y),"Exclude 11 declining-age records")
  add_sensitivity(stratified(d[!d$primary_logic_flag,],y),"Exclude any primary schooling contradiction")
  add_sensitivity(stratified(d[!d$grade_below_5_review,],y),"Exclude sole highest-grade-below-5 review record")
  add_sensitivity(stratified(d[d$cohort=="A_2020",],y),"A2020 only, closest to stated followup horizon")
  # Ordinary FE has implicit weights proportional to observed n_s p_s(1-p_s).
  ff <- robust_fit(as.formula(paste(y,"~ selected + cohort")),d)
  L <- setNames(rep(0,length(ff$coef)),names(ff$coef)); L["selected"] <- 1
  rr <- contrast(ff,L); rr$control_mean <- NA; rr$selected_mean <- NA
  rr$n_control <- sum(model.frame(ff$fit)$selected==0); rr$n_selected <- sum(model.frame(ff$fit)$selected==1); rr$outcome <- y
  add_sensitivity(rr,"Ordinary cohort fixed effects")
  # Common baseline slopes with assignment interactions and cohort-specific treatment effects.
  # Covariates are centered at each full randomized cohort's mean, keeping the target fixed.
  dx <- d
  centered <- character()
  for(v in controls) {
    nv <- paste0(v,"_c"); centered <- c(centered,nv)
    dx[[nv]] <- dx[[v]]-ave(dx[[v]],dx$cohort,FUN=mean)
  }
  formula <- as.formula(paste(y,"~ 0 + cohort + cohort:selected +",paste(centered,collapse=" + "),"+ selected:(",paste(centered,collapse=" + "),")"))
  ff <- robust_fit(formula,dx)
  L <- setNames(rep(0,length(ff$coef)),names(ff$coef))
  for(s in names(weights)) L[paste0("cohort",s,":selected")] <- weights[s]
  rr <- contrast(ff,L); rr$control_mean <- NA; rr$selected_mean <- NA
  rr$n_control <- sum(model.frame(ff$fit)$selected==0); rr$n_selected <- sum(model.frame(ff$fit)$selected==1); rr$outcome <- y
  add_sensitivity(rr,"Baseline-adjusted, assignment-interacted covariates")
}
write_table(do.call(rbind,sensitivity),"sensitivity_effects")
# Save every analysis preparation, including imputed and centered baseline controls.
# dx contains all applicants; lm performs only outcome-specific omission internally.
write.csv(dx,file.path(derived,"adjusted_analysis_data.csv"),row.names=FALSE,na="")

```

## 26. Bound the effect under worst-case missing outcomes

*Original script lines 350-364.*

**Scope note: this chunk retains the earlier supplementary pooled analysis. The current A2020 primary tables begin in section 33.**

For enrollment and private attendance, an unobserved outcome must fall between 0 and 1. For total repetitions, the dictionary gives support from 0 to 3. The lower bound fills every missing selected outcome with its minimum and every missing control outcome with its maximum. The upper bound reverses those assignments.

The calculations use every baseline applicant in the arm denominators and combine the cohort bounds using the fixed baseline shares. Missing highest grade is not bounded here because no highest-grade values are missing in the supplied data, and the dictionary does not specify its support.

These are **identification ranges for missing values, not confidence intervals**. They relax the assumption about missing responses but do not account for sampling/assignment uncertainty, errors in observed values, or uncertain survey timing. A positive lower bound does not by itself establish a statistically significant effect.

**Output:** `missing_outcome_bounds.csv`.

```r
# Worst-case identification bounds for item nonresponse, using dictionary support.
# Bounds are on point identification, not confidence intervals; no MAR assumption.
bounds <- do.call(rbind,lapply(c("in_school_now","in_private_now","total_repeats"),function(y) {
  lower_support <- 0; upper_support <- if(y=="total_repeats") 3 else 1
  lo <- hi <- 0
  for(s in names(weights)) {
    x <- d[d$cohort==s,]; y1 <- x[x$selected==1,y]; y0 <- x[x$selected==0,y]
    m1 <- sum(is.na(y1)); m0 <- sum(is.na(y0))
    lo <- lo+weights[s]*((sum(y1,na.rm=TRUE)+lower_support*m1)/length(y1)-(sum(y0,na.rm=TRUE)+upper_support*m0)/length(y0))
    hi <- hi+weights[s]*((sum(y1,na.rm=TRUE)+upper_support*m1)/length(y1)-(sum(y0,na.rm=TRUE)+lower_support*m0)/length(y0))
  }
  data.frame(outcome=y,lower_bound=lo,upper_bound=hi,support_low=lower_support,support_high=upper_support)
}))
write_table(bounds,"missing_outcome_bounds")

```

## 27. Explore secondary outcomes and the work inconsistency

*Original script lines 365-371.*

**Scope note: this chunk retains the earlier supplementary pooled analysis. The current A2020 primary tables begin in section 33.**

The same cohort-weighted method is applied to 12 additional outcomes covering subsidy use, private-school entry, completion, repetition, school years, marriage, childbearing and work. Holm correction is applied across this separate family of 12 exploratory p-values.

The final line repeats the working and weekly-hours analyses after excluding the no-work/positive-hours conflict. It does not drop people who report working with zero hours. These secondary analyses supplement the four primary outcomes; they do not replace them or establish a mechanism merely because an intermediate variable changes.

**Outputs:** `secondary_effects.csv` and `work_conflict_sensitivity.csv`.

```r
# Secondary outcomes and mechanisms are explicitly exploratory.
secondary_names <- c("receiving_aid_now","started_g6_private","started_g7_private","finished_g6","finished_g7","finished_g8","ever_repeated","years_in_school","married_or_cohab","has_child","working","hours_worked")
secondary <- do.call(rbind,lapply(secondary_names,function(y) stratified(d,y)))
secondary$holm_p <- p.adjust(secondary$p_value,"holm")
write_table(secondary,"secondary_effects")
write_table(do.call(rbind,lapply(c("working","hours_worked"),function(y) stratified(d[!d$work_hours_conflict,],y))),"work_conflict_sensitivity")

```

## 28. Describe follow-up administration and sample composition

*Original script lines 372-376.*

**Scope note: this chunk retains the earlier supplementary pooled analysis. The current A2020 primary tables begin in section 33.**

This chunk compares interview month, survey form, household visits, and reported parental schooling across lottery arms using the same cohort-weighted helper. These variables are diagnostics, not baseline balance measures and not controls in the primary causal model.

It also cross-tabulates cohort, assignment and sex. That table shows the number of applicants in each design cell and supports inspection of the sex-interaction model's comparisons.

**Outputs:** `followup_descriptives.csv` and `cohort_assignment_sex_counts.csv`.

```r
# Diagnostic: post-assignment administrative/household variables are not controls.
admin <- do.call(rbind,lapply(c("survey_month","survey_form","household_visit","mother_educ","father_educ"),function(y) stratified(d,y)))
write_table(admin,"followup_descriptives")
write_table(as.data.frame(with(d,table(cohort,selected,male))),"cohort_assignment_sex_counts")

```

## 29. Plot the four primary effects

*Original script lines 377-391.*

**Scope note: this chunk retains the earlier supplementary pooled analysis. The current A2020 primary tables begin in section 33.**

`draw_effects()` creates two panels: attendance outcomes on the left and grade progression on the right. Binary estimates and confidence limits are multiplied by 100 to show percentage points. The progression outcomes retain their original units.

Dots show point estimates, horizontal segments show ordinary 95% confidence intervals, and the dashed vertical line marks zero effect. Plot settings control panel layout, margins, labels and colors. Calling the same drawing function inside PDF and PNG devices produces both formats, and `dev.off()` closes each file correctly.

These plotted intervals are not Holm-adjusted. **Outputs:** `primary_effects.pdf` and `primary_effects.png`.

```r
# Data graphics use base R only; both PDF and PNG are reproducible.
draw_effects <- function() {
  par(mfrow=c(1,2),mar=c(5,8,3,1),oma=c(0,0,1,0),family="sans")
  for(ix in list(1:2,3:4)) {
    mult <- if(ix[1]==1) 100 else 1
    a <- main[ix,]; yy <- c(2,1); xr <- range(c(0,a$ci_low*mult,a$ci_high*mult))*1.12
    plot(a$estimate*mult,yy,xlim=xr,ylim=c(.5,2.5),axes=FALSE,pch=19,col="#087E8B",xlab=if(mult==100) "Effect (percentage points)" else "Effect (grades)",ylab="",cex=1.3)
    short_labels <- c("Enrolled","Private school","Highest grade","Grade repetitions")
    axis(1); axis(2,at=yy,labels=short_labels[ix],las=1,cex.axis=.85); abline(v=0,lty=2,col="gray60")
    segments(a$ci_low*mult,yy,a$ci_high*mult,yy,lwd=2,col="#087E8B")
    title(if(mult==100) "School attendance" else "Grade progression")
  }
}
pdf(file.path(fig,"primary_effects.pdf"),width=11,height=4.3); draw_effects(); dev.off()
png(file.path(fig,"primary_effects.png"),width=1800,height=720,res=150); draw_effects(); dev.off()
```

## 30. Plot the age-change distribution by cohort

*Original script lines 392-401.*

**Scope note: this chunk retains the earlier supplementary pooled analysis. The current A2020 primary tables begin in section 33.**

This function draws a separate age-change histogram-style bar chart for each cohort. It explicitly includes integer differences from -5 through 7, including values with zero observations, so the displayed bins are comparable. That range covers the supplied age differences; it should be revisited if the data change.

Teal highlights the diagnostic two-to-four-year window, while gray marks changes outside it. Applicants with missing age differences do not enter the bars. Each panel has its own count scale, so compare the location of the distribution rather than bar heights across panels when judging timing.

**Outputs:** `age_changes.pdf` and `age_changes.png`.

```r
draw_age <- function() {
  par(mfrow=c(1,3),mar=c(4.5,4,3,1),family="sans")
  for(s in levels(d$cohort)) {
    vals <- seq(-5,7)
    tab <- table(factor(d$age_change[d$cohort==s],levels=vals))
    barplot(tab,names.arg=vals,col=ifelse(vals%in%2:4,"#087E8B","#8093A6"),border=NA,xlab="Followup age minus baseline age",ylab="Applicants",main=gsub("_"," ",s),cex.names=.8)
  }
}
pdf(file.path(fig,"age_changes.pdf"),width=11,height=4.2); draw_age(); dev.off()
png(file.path(fig,"age_changes.png"),width=1800,height=700,res=150); draw_age(); dev.off()
```

## 31. Plot effects for girls and boys

*Original script lines 402-414.*

**Scope note: this chunk retains the earlier supplementary pooled analysis. The current A2020 primary tables begin in section 33.**

The four panels show the girls' and boys' effect estimates for each primary outcome, with separate colors and ordinary 95% intervals. The plot selects the sex-specific rows and omits the boys-minus-girls contrast row; that direct test remains in the result tables.

Attendance effects are converted to percentage points. Highest grade and repetition effects stay in their original units. The zero line provides a visual reference, but the separate intervals should not replace the formal test of the difference between sexes.

**Outputs:** `sex_effects.pdf` and `sex_effects.png`.

```r
draw_sex <- function() {
  par(mfrow=c(2,2),mar=c(4,5,3,1),family="sans")
  for(y in primary) {
    a <- sex_results[sex_results$outcome==y&sex_results$sex!="Boys minus girls",]
    mult <- if(y%in%c("in_school_now","in_private_now"))100 else 1
    plot(a$estimate*mult,c(2,1),xlim=range(c(0,a$ci_low*mult,a$ci_high*mult))*1.15,ylim=c(.5,2.5),axes=FALSE,pch=19,col=c("#087E8B","#9B5E2E"),xlab=if(mult==100) "Percentage points" else "Grades",ylab="",main=labels[y])
    axis(1); axis(2,at=c(2,1),labels=a$sex,las=1); abline(v=0,lty=2,col="gray60")
    segments(a$ci_low*mult,c(2,1),a$ci_high*mult,c(2,1),lwd=2,col=c("#087E8B","#9B5E2E"))
  }
}
pdf(file.path(fig,"sex_effects.pdf"),width=10,height=7); draw_sex(); dev.off()
png(file.path(fig,"sex_effects.png"),width=1500,height=1050,res=150); draw_sex(); dev.off()

```

## 32. Verify the calculations and record the completed run

*Original script lines 415-429.*

**Scope note: this chunk retains the earlier supplementary pooled analysis. The current A2020 primary tables begin in section 33.**

For each primary outcome, the script independently reconstructs the estimate from cohort-specific selected and control means. It also reconstructs the HC2 variance by summing the weighted within-arm sample variances divided by their observed sample sizes.

`stopifnot()` checks agreement with the regression results to within `1e-9`. It also verifies the expected 1,618 applicants, positive main standard errors, and correctly ordered interval limits. The sample-size assertion is intentionally specific to this supplied assessment dataset.

Finally, `sessionInfo()` records the R environment, a completion note is written, and the main table is printed. These checks establish numerical consistency; they do not verify the lottery procedure, resolve contradictory reports, or independently hash raw files. Source hashes are provided separately in the package documentation.

**Outputs:** `results/session_info.txt`, `results/verification.txt`, and the printed primary results.

```r
# Explicit output verification: counts, nonnegative variances, hand-computed primary effects.
for(i in seq_along(primary)) {
  y <- primary[i]; mu <- vv <- 0
  for(s in names(weights)) {
    x <- d[d$cohort==s,]; t <- na.omit(x[x$selected==1,y]); c <- na.omit(x[x$selected==0,y])
    mu <- mu+weights[s]*(mean(t)-mean(c))
    vv <- vv+weights[s]^2*(var(t)/length(t)+var(c)/length(c))
  }
  stopifnot(abs(mu-main$estimate[i])<1e-9,abs(sqrt(vv)-main$se[i])<1e-9)
}
stopifnot(nrow(d)==1618,all(main$se>0),all(main$ci_low<main$ci_high))
writeLines(capture.output(sessionInfo()),file.path(root,"results/session_info.txt"))
writeLines(c("Analysis finished successfully.","Raw originals unchanged. All outputs generated from raw CSVs.","Primary HC2 covariance equals independent stratified sample-variance formula."),file.path(root,"results/verification.txt"))
print(main[,c("outcome","estimate","se","ci_low","ci_high","p_value","holm_p","n")],row.names=FALSE)

```

## 33. Set the current scope and estimate the five policy outcomes

*Original script lines 430-463.*

This is the beginning of the **current primary analysis**. It estimates A2020 on its own and reports A2022 and B2018 as separate checks. `policy` contains school years since allocation, marriage/cohabitation, parenthood, employment and weekly hours. `primary`, defined earlier, retains the four schooling outcomes. Both sets are offer effects: selected minus nonselected applicant means within each lottery.

`cohort_itt()` reuses the earlier robust estimator. It suppresses standard errors, intervals and p-values when an entire cohort has no outcome variation. A2022 has no observed marriage/cohabitation or parenthood events; a zero-width sandwich interval would falsely imply certainty. Observed means and the zero sample contrast remain visible.

Holm correction is applied separately to the five policy and four schooling outcomes, within each cohort. The nominal family sizes remain five and four even if a test is not reported. A second `holm_all_nine_p` column checks the broader nine-outcome family. These families were chosen during the draft revision, not prospectively registered. None of the five A2020 policy effects passes the five-test correction.

**Outputs:** `revised_policy_effects.csv` and `revised_schooling_effects.csv`.

```r
# REVISION 1: Define A2020 as primary and keep other cohorts separate.
policy <- c("years_in_school","married_or_cohab","has_child","working","hours_worked")
all_outcomes <- c(policy,primary)
policy_labels <- c(years_in_school="School years completed since allocation",married_or_cohab="Married or cohabiting",has_child="Has a child",working="Working",hours_worked="Weekly hours worked")
all_labels <- c(policy_labels,labels)
binary_outcomes <- c("married_or_cohab","has_child","working","in_school_now","in_private_now")
scope <- function(s) if(s=="A_2020") "Primary: A2020 applicants" else "Separate cohort check"
# Constant binary outcomes need explicit handling: zero observed events is not
# evidence of zero population effect or a zero-width confidence interval.
cohort_itt <- function(x,y,hc="HC2") {
  r <- stratified(x,y,hc)
  constant <- length(unique(na.omit(x[[y]])))<2
  r$inference_status <- if(constant) "Not reported: no observed outcome variation" else paste0(hc,"/t approximation")
  if(constant) r[,c("se","ci_low","ci_high","p_value")] <- NA_real_
  r
}
rev_all <- do.call(rbind,lapply(levels(d$cohort),function(s) do.call(rbind,lapply(all_outcomes,function(y) {
  r <- cohort_itt(d[d$cohort==s,],y); r$cohort <- s; r$scope <- scope(s)
  r$label <- all_labels[y]; r$family <- if(y%in%policy) "Five policy outcomes" else "Four schooling outcomes"
  r$unit <- if(y%in%binary_outcomes) "proportion" else if(y=="hours_worked") "hours/week" else if(y=="years_in_school") "school years" else "grades/counts"
  r
}))))
rev_all$holm_p <- rev_all$holm_all_nine_p <- NA_real_
for(s in levels(d$cohort)) {
  for(yy in list(policy,primary)) {
    ix <- rev_all$cohort==s&rev_all$outcome%in%yy
    rev_all$holm_p[ix] <- p.adjust(rev_all$p_value[ix],"holm",n=length(yy))
  }
  ix <- rev_all$cohort==s
  rev_all$holm_all_nine_p[ix] <- p.adjust(rev_all$p_value[ix],"holm",n=9)
}
write_table(rev_all[rev_all$outcome%in%policy,],"revised_policy_effects")
write_table(rev_all[rev_all$outcome%in%primary,],"revised_schooling_effects")

```

## 34. Check balance and missing outcomes within each cohort

*Original script lines 464-513.*

Balance is now checked within each lottery rather than averaged across cohorts. The first loop estimates selected-minus-control baseline differences and scales them by the square root of the average arm variance. An initial joint test regresses selection on the nonconstant baseline controls and tests their coefficients together with an HC2-robust F approximation. This is retained as a secondary diagnostic because sparse groups can make the Wald approximation unstable: all five A2022 applicants with missing baseline age are controls.

The preferred joint check uses a Mahalanobis distance between baseline arm means, with covariance fixed from all applicants in that cohort. It repeatedly reassigns selection labels while preserving the cohort's observed arm counts. Baseline values and imputation remain fixed because neither depends on the permuted labels. With seed 20260922 and 9,999 draws, the add-one Monte Carlo p-value is `(1 + number of permuted distances at least as large as observed) / 10000`. A2020, A2022 and B2018 p-values are 0.6038, 0.1162 and 0.0152. These calibrate balance under the stated complete lottery conditional on arm sizes; they cannot prove actual random assignment. Monte Carlo standard errors are saved.

The missingness loop treats an indicator for a missing response as its own outcome. It also saves the missing and observed counts in each arm for all nine outcomes. A matched follow-up record does not imply that every question was answered. Complete-outcome estimates need observed responses to represent the assigned groups; small missing counts alone cannot prove that assumption.

**Outputs:** `revised_baseline_balance.csv`, `revised_balance_joint_test.csv`, `revised_balance_permutation.csv`, and `revised_missingness.csv`.

```r
# REVISION 2: Diagnose baseline comparability and item nonresponse by cohort.
rev_balance <- list(); rev_joint <- list(); rev_missing <- list()
for(s in levels(d$cohort)) {
  x <- d[d$cohort==s,]
  for(y in balance_vars) {
    r <- cohort_itt(x,y); r$cohort <- s
    denom <- sqrt((var(x[x$selected==0,y],na.rm=TRUE)+var(x[x$selected==1,y],na.rm=TRUE))/2)
    r$standardized_difference <- if(is.finite(denom)&&denom>0) r$estimate/denom else NA_real_
    rev_balance[[length(rev_balance)+1]] <- r
  }
  cc <- controls[vapply(x[controls],function(v) length(unique(v))>1,logical(1))]
  fit <- robust_fit(as.formula(paste("selected ~",paste(cc,collapse=" + "))),x)
  bb <- fit$coef[cc]; VV <- fit$V[cc,cc,drop=FALSE]; q <- length(cc)
  Fval <- as.numeric(t(bb)%*%solve(VV,bb))/q
  rev_joint[[length(rev_joint)+1]] <- data.frame(cohort=s,F_statistic=Fval,numerator_df=q,denominator_df=fit$df,p_value=pf(Fval,q,fit$df,lower.tail=FALSE),n=fit$n)
  for(y in all_outcomes) {
    x$item_missing <- as.integer(is.na(x[[y]])); r <- stratified(x,"item_missing")
    r$outcome <- y; r$cohort <- s
    r$missing_control <- sum(is.na(x[[y]])&x$selected==0); r$missing_selected <- sum(is.na(x[[y]])&x$selected==1)
    r$observed_control <- sum(!is.na(x[[y]])&x$selected==0); r$observed_selected <- sum(!is.na(x[[y]])&x$selected==1)
    rev_missing[[length(rev_missing)+1]] <- r
  }
}
write_table(do.call(rbind,rev_balance),"revised_baseline_balance")
write_table(do.call(rbind,rev_joint),"revised_balance_joint_test")
write_table(do.call(rbind,rev_missing),"revised_missingness")
# Prefer this conditional randomization balance check to a sparse-cell Wald test.
# In A2022 all five baseline-age-missing applicants are controls. The selection
# regression nearly fits that cell perfectly, making its robust Wald test unstable.
# Hold baseline X and each cohort's selected count fixed; reassign lottery labels.
set.seed(20260922)
B_perm <- 9999L
rev_perm <- list()
for(s in levels(d$cohort)) {
  x <- d[d$cohort==s,]; n <- nrow(x); n1 <- sum(x$selected==1); n0 <- n-n1
  cc <- controls[vapply(x[controls],function(v) length(unique(v))>1,logical(1))]
  X <- scale(as.matrix(x[cc]),center=TRUE,scale=FALSE)
  Vdiff <- (1/n1+1/n0)*cov(X); invV <- solve(Vdiff)
  statistic <- function(selected_ids) {
    dif <- colSums(X[selected_ids,,drop=FALSE])*(1/n1+1/n0)
    as.numeric(t(dif)%*%invV%*%dif)
  }
  observed <- statistic(which(x$selected==1))
  null <- replicate(B_perm,statistic(sample.int(n,n1,replace=FALSE)))
  exceed <- sum(null>=observed-1e-12); p <- (1+exceed)/(B_perm+1)
  rev_perm[[length(rev_perm)+1]] <- data.frame(cohort=s,n=n,n_selected=n1,n_control=n0,covariates=length(cc),mahalanobis_statistic=observed,permutations=B_perm,p_value=p,monte_carlo_se=sqrt(p*(1-p)/(B_perm+1)),
    note="Conditional complete-randomization check with fixed arm counts; assumes the stated applicant lottery. Sparse-cell HC2 Wald result is secondary.")
}
write_table(do.call(rbind,rev_perm),"revised_balance_permutation")

```

## 35. Test sensitivity to data issues, controls and missing binary outcomes

*Original script lines 514-545.*

For every A2020 outcome, the script saves the main estimate, separate exclusions for declining ages, schooling contradictions and the work-hours conflict, an HC3 interval, and an adjusted estimate. Exclusions apply only to the named issue, never to every review flag. Some flagged records may already lack the particular outcome, so the change in model N can be smaller than the number of flagged applicants.

The adjusted offer-effect model centers baseline controls using **all randomized A2020 applicants** and interacts those controls with selection. The coefficient on `selected` then describes the contrast at those fixed baseline means. Missing baseline age and SES were already replaced by cohort means with missingness indicators. No outcome, school choice or current aid is used as an adjustment control.

The final loop gives worst-case missing-data bounds for binary outcomes using their logical 0/1 limits. For the lower bound, missing selected outcomes are set to zero and missing control outcomes to one; the upper bound reverses that assignment. These are bounds on the sample mean contrast, not confidence intervals. No unsupported upper limit is invented for school years or hours.

**Outputs:** `revised_policy_sensitivity.csv` (all nine outcomes despite its filename) and `revised_binary_missing_bounds.csv`.

```r
# REVISION 3: Check the primary A2020 results against data and model choices.
a20 <- d[d$cohort=="A_2020",]
rev_sens <- list()
for(y in all_outcomes) {
  samples <- list("Primary observed outcome"=a20,"Exclude declining-age records"=a20[!a20$age_decreased,],
    "Exclude schooling contradictions"=a20[!a20$primary_logic_flag,],"Exclude work-hours contradiction"=a20[!a20$work_hours_conflict,])
  for(nm in names(samples)) {
    r <- cohort_itt(samples[[nm]],y); r$specification <- nm; r$cohort <- "A_2020"
    rev_sens[[length(rev_sens)+1]] <- r
  }
  r <- cohort_itt(a20,y,"HC3"); r$specification <- "HC3 standard errors"; r$cohort <- "A_2020"
  rev_sens[[length(rev_sens)+1]] <- r
  xx <- a20; cc <- character()
  for(v in controls) {nm <- paste0(v,"_centered"); xx[[nm]] <- xx[[v]]-mean(xx[[v]]); cc <- c(cc,nm)}
  fit <- robust_fit(as.formula(paste(y,"~ selected * (",paste(cc,collapse=" + "),")")),xx)
  L <- setNames(rep(0,length(fit$coef)),names(fit$coef)); L["selected"] <- 1
  r <- contrast(fit,L); r$control_mean <- r$selected_mean <- NA_real_
  mf <- model.frame(fit$fit); r$n_control <- sum(mf$selected==0); r$n_selected <- sum(mf$selected==1)
  r$outcome <- y; r$inference_status <- "HC2/t approximation"; r$specification <- "Baseline adjustment with assignment interactions"; r$cohort <- "A_2020"
  rev_sens[[length(rev_sens)+1]] <- r
}
write_table(do.call(rbind,rev_sens),"revised_policy_sensitivity")
# For binary outcomes only, use logical 0/1 limits, not the observed range.
rev_bounds <- do.call(rbind,lapply(binary_outcomes,function(y) {
  n1 <- sum(a20$selected==1); n0 <- sum(a20$selected==0)
  s1 <- sum(a20[a20$selected==1,y],na.rm=TRUE); s0 <- sum(a20[a20$selected==0,y],na.rm=TRUE)
  m1 <- sum(is.na(a20[a20$selected==1,y])); m0 <- sum(is.na(a20[a20$selected==0,y]))
  data.frame(cohort="A_2020",outcome=y,lower=s1/n1-(s0+m0)/n0,upper=(s1+m1)/n1-s0/n0,
    missing_selected=m1,missing_control=m0,note="Logical missing-outcome bounds; not confidence intervals")
}))
write_table(rev_bounds,"revised_binary_missing_bounds")

```

## 36. Compare effects for girls and boys in A2020

*Original script lines 546-565.*

The model `Y ~ selected * male` estimates separate arm differences for girls and boys. Girls' effect is the selection coefficient, boys' effect adds the selection-by-male interaction, and the interaction alone is the direct boys-minus-girls test. This is the correct comparison of effects; one subgroup being significant and another nonsignificant is not a test of a difference.

The HC2 covariance supplies uncertainty for each linear contrast. `n` is the full model sample and `subgroup_n` identifies the observations belonging to the stated sex. Holm correction applies to the five policy interaction tests and separately to the four schooling interaction tests. These are exploratory subgroup analyses.

**Output:** `revised_sex_effects.csv`.

```r
# REVISION 4: Retain sex heterogeneity using direct within-cohort interactions.
rev_sex <- list()
for(y in all_outcomes) {
  fit <- robust_fit(as.formula(paste(y,"~ selected * male")),a20)
  for(gr in c("Girls","Boys","Boys minus girls")) {
    L <- setNames(rep(0,length(fit$coef)),names(fit$coef))
    if(gr!="Boys minus girls") L["selected"] <- 1
    if(gr!="Girls") L["selected:male"] <- 1
    r <- contrast(fit,L); r$outcome <- y; r$sex <- gr; r$cohort <- "A_2020"
    r$subgroup_n <- sum(!is.na(a20[[y]]) & if(gr=="Boys minus girls") TRUE else a20$male==as.integer(gr=="Boys"))
    rev_sex[[length(rev_sex)+1]] <- r
  }
}
rev_sex <- do.call(rbind,rev_sex); rev_sex$holm_interaction_p <- NA_real_
for(yy in list(policy,primary)) {
  ix <- rev_sex$sex=="Boys minus girls"&rev_sex$outcome%in%yy
  rev_sex$holm_interaction_p[ix] <- p.adjust(rev_sex$p_value[ix],"holm",n=length(yy))
}
write_table(rev_sex,"revised_sex_effects")

```

## 37. Save observed private-school exits and all school histories

*Original script lines 566-586.*

This chunk preserves the three reported private-school indicators: entry to grade 6, entry to grade 7, and current attendance. A question mark in a history means missing, never zero. Two flags identify current nonprivate status following reported private attendance in G6, or in either G6/G7. The record-level files include applicant IDs, assignment, schooling and aid values for inspection.

For each cohort and assignment arm, the transition table counts prior-private applicants, those with observed later status, missing later status, and observed exits. Exit fractions use only paired observed statuses. Current enrollment further describes exits; a person who is no longer enrolled might have completed school, so the code does not label that person a dropout.

These are descriptive histories, **not identified IV defiers**. G6 choice occurs after assignment. A defier would attend privately without an offer but not with an offer at the same horizon; only one of those counterfactuals is observed. Comparing conditional exit fractions does not identify a causal retention effect because starting-private status is itself affected by assignment.

**Outputs:** `private_school_transitions.csv`, `private_school_exit_records.csv`, and `revised_transition_summary.csv`.

```r
# REVISION 5: Describe private-school histories without labeling anyone a defier.
tr <- d[,c("applicant_id","cohort","selected","male","started_g6_private","started_g7_private","in_private_now","in_school_now","highest_grade","years_in_school","receiving_aid_now")]
fmt_status <- function(x) ifelse(is.na(x),"?",as.character(x))
tr$history_g6_g7_current <- paste(fmt_status(tr$started_g6_private),fmt_status(tr$started_g7_private),fmt_status(tr$in_private_now),sep=" -> ")
tr$g6_private_current_nonprivate <- with(tr,!is.na(started_g6_private)&started_g6_private==1&!is.na(in_private_now)&in_private_now==0)
tr$ever_g6_g7_private_current_nonprivate <- with(tr,((!is.na(started_g6_private)&started_g6_private==1)|(!is.na(started_g7_private)&started_g7_private==1))&!is.na(in_private_now)&in_private_now==0)
tr$current_status <- ifelse(is.na(tr$in_school_now),"Enrollment unknown",ifelse(tr$in_school_now==1,"Currently enrolled","Not currently enrolled; completion or exit unknown"))
write.csv(tr,file.path(derived,"private_school_transitions.csv"),row.names=FALSE,na="")
write.csv(tr[tr$ever_g6_g7_private_current_nonprivate,],file.path(derived,"private_school_exit_records.csv"),row.names=FALSE,na="")
rev_tr <- list()
for(s in levels(d$cohort)) for(z in 0:1) {
  x <- tr[tr$cohort==s&tr$selected==z,]
  for(pair in list(c("started_g6_private","started_g7_private"),c("started_g6_private","in_private_now"),c("started_g7_private","in_private_now"))) {
    base <- !is.na(x[[pair[1]]])&x[[pair[1]]]==1
    known <- base&!is.na(x[[pair[2]]]); exits <- known&x[[pair[2]]]==0
    rev_tr[[length(rev_tr)+1]] <- data.frame(cohort=s,selected=z,from=pair[1],to=pair[2],prior_private=sum(base),paired_observed=sum(known),later_unknown=sum(base&is.na(x[[pair[2]]])),
      exits=sum(exits),exit_fraction=sum(exits)/sum(known),exits_currently_enrolled=sum(exits&!is.na(x$in_school_now)&x$in_school_now==1),exits_not_currently_enrolled=sum(exits&!is.na(x$in_school_now)&x$in_school_now==0),exits_enrollment_unknown=sum(exits&is.na(x$in_school_now)))
  }
}
write_table(do.call(rbind,rev_tr),"revised_transition_summary")

```

## 38. Measure the instrument first stage and describe current aid

*Original script lines 587-595.*

For each cohort, this loop estimates the lottery-offer effect on private attendance at G6 entry, G7 entry and follow-up. It saves the control and selected means, effect, HC2 interval and a one-instrument robust F statistic equal to the squared first-stage t statistic. These rows use everyone with the respective school indicator observed; the following outcome-specific IV models may use slightly smaller samples.

`receiving_aid_now` is included as a descriptive offer effect on **any current education aid**. It is not verified original subsidy receipt and must not be used to manufacture a recipient ATT. Relevance is only one IV requirement: a positive or strong first stage cannot establish exclusion or monotonicity.

**Output:** `revised_first_stage.csv`.

```r
# REVISION 6: Estimate first stages, including entry and current attendance.
exposures <- c("in_private_now","started_g6_private","started_g7_private")
rev_fs <- do.call(rbind,lapply(levels(d$cohort),function(s) do.call(rbind,lapply(c(exposures,"receiving_aid_now"),function(y) {
  r <- cohort_itt(d[d$cohort==s,],y); r$cohort <- s; r$F_statistic <- (r$estimate/r$se)^2
  r$interpretation <- if(y=="receiving_aid_now") "Any current aid; not original program receipt" else "Lottery-offer effect on private-school indicator"
  r
}))))
write_table(rev_fs,"revised_first_stage")

```

## 39. Construct confidence sets that allow weak instruments

*Original script lines 596-611.*

For a proposed private-school effect `b`, the reduced-form effect of the lottery on `Y - bD` should be zero under a valid instrument. The AR-type test accepts values satisfying `(RF - b FS)^2 <= tcrit^2 Var(RF - b FS)`. Expanding this inequality gives a quadratic in `b`.

`ar_set()` solves that quadratic without forcing the answer to be an ordinary finite interval. Depending on the information in the first stage, the confidence set can be bounded, disjoint, a half-line, all real numbers, or empty. It returns both numerical endpoints and an explicit type; the endpoints of a disjoint set describe the excluded middle, not a bounded accepted interval. The following chunk suppresses this inference for constant outcomes.

These are heteroskedasticity-robust **approximate AR-type** sets using a t reference, not exact finite-sample randomization sets. They address weak first-stage uncertainty; they do not repair a violation of the IV assumptions.

```r
# REVISION 7: Invert the robust reduced-form test for a weak-IV confidence set.
# AR-type inversion accepts b when (RF-b FS)^2 <= tcrit^2 Var(RF-b FS).
# It allows bounded, disjoint, half-line, empty and all-real confidence sets.
ar_set <- function(A,B,C) {
  tol <- 1e-12
  if(abs(A)<tol) {
    if(abs(B)<tol) return(list(type=if(C<=0) "all real" else "empty",low=NA_real_,high=NA_real_,text=if(C<=0) "All real numbers" else "Empty set"))
    r <- -C/B
    return(list(type="half-line",low=if(B>0) -Inf else r,high=if(B>0) r else Inf,text=if(B>0) sprintf("(-Inf, %.6f]",r) else sprintf("[%.6f, Inf)",r)))
  }
  disc <- B^2-4*A*C
  if(disc<0) return(list(type=if(A<0) "all real" else "empty",low=NA_real_,high=NA_real_,text=if(A<0) "All real numbers" else "Empty set"))
  rr <- sort(c((-B-sqrt(disc))/(2*A),(-B+sqrt(disc))/(2*A)))
  list(type=if(A>0) "bounded" else "disjoint",low=rr[1],high=rr[2],text=if(A>0) sprintf("[%.6f, %.6f]",rr[1],rr[2]) else sprintf("(-Inf, %.6f] U [%.6f, Inf)",rr[1],rr[2]))
}

```

## 40. Estimate schooling IV effects on exactly matched samples

*Original script lines 612-654.*

`iv_fit()` keeps applicants observed on the outcome, the chosen private-school indicator and lottery selection. Both reduced-form regressions use **that identical sample and design matrix**: one regresses the outcome on selection, and the other regresses private attendance on selection. The unadjusted just-identified IV estimate is `RF / FS`. It may differ from dividing the earlier policy ITT by the earlier overall first stage because those tables need not use the same observations.

The joint HC2 covariance retains uncertainty in RF, uncertainty in FS, and their covariance. The delta variance is `(Var(RF) + b^2 Var(FS) - 2 b Cov(RF,FS)) / FS^2`. This is not the naive standard error from regressing the outcome on fitted private attendance. HC2 uses the leverage of the instrument/reduced-form design. The AR-type set is calculated from the same covariance, and `ar_p_zero` tests an effect of zero through the reduced form.

The script repeats the calculation with additive baseline controls as a sensitivity and with G6/G7 entry indicators as alternative treatment definitions. Each definition changes the estimand and exclusion assumption. The adjusted IV is additive, unlike the assignment-interacted offer-effect sensitivity in section 35. All controls were measured at baseline; there are no post-assignment controls.

Interpretation as a private-school complier effect requires randomized selection, relevance, exclusion, monotonicity, no relevant interference between applicants, a sufficiently well-defined schooling exposure and an appropriate missing-data assumption. Current private attendance is only a snapshot. Fee relief, renewal incentives and earlier schooling can affect outcomes through channels not captured by this snapshot. Thus the numerical results are exploratory, assumption-dependent LATE estimates, not private-school ATT or subsidy-recipient ATT. For binary outcomes, estimates are probability differences; they are not odds ratios.

Holm correction is applied to five AR tests within each cohort, schooling definition and adjustment specification. Constant A2022 family outcomes retain zero sample ratios but no uncertainty or p-value is reported.

**Outputs:** `revised_iv_effects.csv` and `revised_iv_entry_sensitivity.csv`.

```r
# REVISION 8: Fit joint reduced forms on an identical Y/D/assignment sample.
# Additive baseline-adjusted IV is a sensitivity, using pre-offer covariates only.
# HC2 uses leverage in the instrument/reduced-form regression, not a naive
# second-stage regression on fitted D. The RF/FS covariance is retained.
iv_fit <- function(x,y,exposure,adjusted=FALSE) {
  ok <- complete.cases(x[,c(y,exposure,"selected")]); xx <- x[ok,]
  X <- cbind(intercept=1,selected=xx$selected)
  if(adjusted) {
    cc <- controls[vapply(x[controls],function(v) length(unique(v))>1,logical(1))]
    X <- cbind(X,as.matrix(xx[cc]))
  }
  qrX <- qr(X); X <- X[,qrX$pivot[seq_len(qrX$rank)],drop=FALSE]
  yy <- cbind(Y=xx[[y]],D=xx[[exposure]])
  fit <- lm.fit(X,yy); bread <- solve(crossprod(X)); h <- rowSums((X%*%bread)*X)
  influence <- (X%*%bread)[,"selected"]/sqrt(pmax(1-h,1e-10))
  V <- crossprod(fit$residuals*as.numeric(influence))
  rf <- unname(fit$coefficients["selected","Y"]); fs <- unname(fit$coefficients["selected","D"])
  beta <- rf/fs; n <- nrow(X); df <- n-ncol(X); crit <- qt(.975,df)
  se <- sqrt(max(0,V[1,1]+beta^2*V[2,2]-2*beta*V[1,2]))/abs(fs)
  ar <- ar_set(fs^2-crit^2*V[2,2],-2*rf*fs+2*crit^2*V[1,2],rf^2-crit^2*V[1,1])
  constant <- length(unique(xx[[y]]))<2
  # Constant outcomes give a misleading degenerate sandwich; suppress inference.
  status <- if(constant) "Not reported: no observed outcome variation" else "Exploratory; valid-IV assumptions required"
  if(constant) ar <- list(type="not reported",low=NA_real_,high=NA_real_,text=status)
  data.frame(cohort=as.character(x$cohort[1]),outcome=y,exposure=exposure,baseline_adjusted=adjusted,n=n,n_control=sum(xx$selected==0),n_selected=sum(xx$selected==1),df=df,
    reduced_form=rf,reduced_form_se=sqrt(V[1,1]),first_stage=fs,first_stage_se=sqrt(V[2,2]),first_stage_F=fs^2/V[2,2],
    estimate=beta,se=if(constant) NA_real_ else se,ci_low=if(constant) NA_real_ else beta-crit*se,ci_high=if(constant) NA_real_ else beta+crit*se,
    p_value=if(constant) NA_real_ else 2*pt(-abs(beta/se),df),ar_p_zero=if(constant) NA_real_ else 2*pt(-abs(rf/sqrt(V[1,1])),df),
    ar_type=ar$type,ar_low=ar$low,ar_high=ar$high,ar_set=ar$text,var_rf=V[1,1],var_fs=V[2,2],cov_rf_fs=V[1,2],inference_status=status)
}
rev_iv_rows <- list()
for(s in levels(d$cohort)) for(exposure in exposures) for(y in policy) for(adj in c(FALSE,TRUE)) {
  rev_iv_rows[[length(rev_iv_rows)+1]] <- iv_fit(d[d$cohort==s,],y,exposure,adj)
}
rev_iv <- do.call(rbind,rev_iv_rows)
rev_iv$holm_ar_p <- NA_real_
for(s in levels(d$cohort)) for(exposure in exposures) for(adj in c(FALSE,TRUE)) {
  ix <- rev_iv$cohort==s&rev_iv$exposure==exposure&rev_iv$baseline_adjusted==adj
  rev_iv$holm_ar_p[ix] <- p.adjust(rev_iv$ar_p_zero[ix],"holm",n=5)
}
write_table(rev_iv[rev_iv$exposure=="in_private_now",],"revised_iv_effects")
write_table(rev_iv[rev_iv$exposure!="in_private_now",],"revised_iv_entry_sensitivity")

```

## 41. Verify revised results and draw the A2020 policy chart

*Original script lines 655-679.*

The script independently reconstructs all cohort-specific offer effects and nondegenerate HC2 standard errors from arm means and sample variances. It verifies that each IV sample size equals its arm counts and checks the 150 selected A2020 G6-private/current-nonprivate histories. Separate independent scripts additionally compare the full set of IV models.

The chart groups binary outcomes in percentage points and keeps school years and weekly hours on their own scales. Its intervals are ordinary 95% intervals, not simultaneous intervals adjusted for multiple testing. The verification note explicitly identifies `revised_*` tables and A2020 as the current primary scope. Earlier pooled outputs are retained only as supplementary results.

**Outputs:** `revised_A2020_policy.pdf`, `revised_A2020_policy.png`, and the updated verification note.

```r
# REVISION 9: Check the new estimators and draw the five A2020 policy outcomes.
for(i in seq_len(nrow(rev_all))) {
  r <- rev_all[i,]; x <- d[d$cohort==r$cohort,]
  y0 <- na.omit(x[x$selected==0,r$outcome]); y1 <- na.omit(x[x$selected==1,r$outcome])
  stopifnot(abs(mean(y1)-mean(y0)-r$estimate)<1e-10)
  if(is.finite(r$se)) stopifnot(abs(sqrt(var(y1)/length(y1)+var(y0)/length(y0))-r$se)<1e-10)
}
stopifnot(all(rev_iv$n==rev_iv$n_selected+rev_iv$n_control),all(is.finite(rev_iv$estimate)),sum(tr$g6_private_current_nonprivate&tr$cohort=="A_2020"&tr$selected==1)==150)
draw_policy <- function() {
  par(mfrow=c(1,3),mar=c(5,7,3,1),family="sans")
  groups <- list(c("married_or_cohab","has_child","working"),"years_in_school","hours_worked")
  for(ys in groups) {
    x <- rev_all[rev_all$cohort=="A_2020"&rev_all$outcome%in%ys,]; yy <- rev(seq_len(nrow(x)))
    mult <- if(ys[1]%in%binary_outcomes) 100 else 1
    xr <- range(c(0,x$ci_low*mult,x$ci_high*mult)); pad <- diff(xr)*.15
    plot(x$estimate*mult,yy,xlim=xr+c(-pad,pad),ylim=c(.5,nrow(x)+.5),axes=FALSE,pch=19,col="#087E8B",xlab=if(mult==100) "Percentage points" else if(ys[1]=="hours_worked") "Hours/week" else "School years",ylab="")
    axis(1); axis(2,at=yy,labels=c(married_or_cohab="Married/cohabiting",has_child="Has child",working="Working",years_in_school="School years",hours_worked="Work hours")[x$outcome],las=1,cex.axis=.8)
    abline(v=0,lty=2,col="gray60"); segments(x$ci_low*mult,yy,x$ci_high*mult,yy,col="#087E8B",lwd=2)
    title("A2020 offer effect",cex.main=.9)
  }
}
pdf(file.path(fig,"revised_A2020_policy.pdf"),width=12,height=4); draw_policy(); dev.off()
png(file.path(fig,"revised_A2020_policy.png"),width=2100,height=700,res=175); draw_policy(); dev.off()
writeLines(c("Analysis finished successfully.","Current scope: revised_* tables, primary A2020; A2022 and B2018 separate checks.","Original pooled tables retained as supplementary, not current primary results.","Raw originals unchanged; direct arm means and HC2 variances checked.","IV uses exact common samples, joint RF/FS covariance and AR-type confidence sets.","No observed exit is labeled an identified defier; actual subsidy-recipient ATT is not identified."),file.path(root,"results/verification.txt"))
print(rev_all[rev_all$cohort=="A_2020",c("outcome","estimate","ci_low","ci_high","p_value","holm_p","n")],row.names=FALSE)
```

## A short guide to the recurring R syntax

| Syntax | How it works here |
| --- | --- |
| `d[[v]]` | Selects a column whose name is stored in the string `v`. |
| `d[condition, ]` | Selects rows satisfying a logical condition, keeping all columns. |
| `!is.na(x)` | Identifies observed values. Missing is different from zero. |
| `lapply(items, function(...))` | Repeats a calculation and returns its results as a list. |
| `do.call(rbind, results)` | Stacks a list of result rows or tables vertically. |
| `paste()` / `paste0()` | Builds column names, formula text, and descriptive labels. |
| `factor()` | Creates an explicit categorical variable for regression or tabulation. |
| `as.formula()` | Converts constructed text into an R regression formula. |
| `A:B` in a formula | Includes an interaction between regressors or categories. |
| `%*%`, `t()`, `crossprod()` | Matrix multiplication, transpose, and matrix cross-products. |
| `stopifnot()` | Stops execution when an essential condition fails. |

## How to read the main result columns

In offer-effect tables, `estimate` is selected minus control. In `revised_iv_effects.csv` and `revised_iv_entry_sensitivity.csv`, it is the exploratory IV ratio. `se` is the reported robust standard error and `ci_low`/`ci_high` are ordinary 95% interval endpoints. `p_value` is the unadjusted two-sided p-value, while `holm_p` applies the stated offer-effect family correction. `n` counts observations used for that outcome. Current `revised_*` offer tables report within-cohort arm means; earlier supplementary pooled tables standardize means to baseline cohort shares.

For IV, prefer examining `ar_type` and `ar_set` alongside the conventional interval. `ar_p_zero` is the AR-type test of a zero effect, and `holm_ar_p` corrects those five tests within a cohort, treatment definition and adjustment specification. `ar_low`/`ar_high` are a bounded interval only when `ar_type` says `bounded`; disjoint sets accept values outside the two endpoints. Blank inference fields for constant outcomes mean inference was suppressed, not zero uncertainty. IV has its own `reduced_form`, `first_stage` and arm counts so that the exact common sample can be checked.

For the sex table, `n` refers to the entire fitted model; `subgroup_n` provides the sex-specific count. For sensitivity rows, a blank standardized mean means that the script does not calculate or report that quantity for that specification, not that the mean is zero.

The missingness-bounds table is different: its endpoints describe what missing outcomes could do within the permitted outcome range. They are not 95% confidence limits.
