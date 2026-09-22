# Code for the results shown in the slides

This focused companion reproduces the numerical evidence in the **24-slide DIL deck**: its displayed regressions, p-values, chart inputs, data checks and descriptive tables. It reads the two original study CSVs directly and does not source the longer `run_analysis.R`. It fits only the specifications used in the presentation. Supporting sample counts and model-coding diagnostics make those results auditable; the comprehensive audit and undisplayed specifications remain outside this file.

**Primary sample:** all A2020 applicants, pooled across application ages. A2022 and B2018 remain separate checks. Application-age groups are an additional exploratory breakdown; they are not verified grades. The user selected ages 10–11, 12–13 and 14–18 after reviewing the draft. Controlled models add baseline covariates and separate SES and neighborhood fixed effects. None of these revised choices is described as preregistered.

**Group labels:** “Control group mean” means `selected = 0`; “Treatment group mean” means `selected = 1`, meaning selected in the subsidy lottery. Membership does not establish actual subsidy receipt or private-school attendance. Means on slides 5 and 6 use the same observed-outcome sample as the corresponding unadjusted offer regression. Raw group means do not subtract to a controlled regression coefficient.

## What this code reproduces

| Slides | Displayed evidence | Output files (under `results/slide_regressions/`) |
| --- | --- | --- |
| 5, 6, 14 | A2020 nine offer effects and five policy effects per comparison cohort | `itt.csv` |
| 9, 11 | Three current-private first stages, chart means and uptake levels for ATT | `first_stages.csv` |
| 12, 19 | Five main A2020 IV effects and three additional hours specifications | `iv.csv` |
| 18 | Five policy outcomes under three sensitivity specifications; primary effects reuse ITT | `policy_sensitivity.csv` |
| 7, 20 | Main schooling sex discussion and all nine appendix sex contrasts | `sex.csv` |
| 8, 22 | Policy and schooling effects by application-age group, plus equality tests | `age_groups.csv`, `age_effects.csv`, `age_heterogeneity.csv` |
| 23, 24 | Nine controlled offer effects and five controlled IV effects, with coding diagnostics | `fe_itt.csv`, `fe_iv.csv`, `fe_category_counts.csv` |
| 2, 3, 4, 10, 16, 17 | Cohorts, data checks, credibility caveats, exits, missingness and record examples | `cohort_summary.csv`, `audit_counts.csv`, `transitions.csv`, `policy_missingness.csv`, `record_examples.csv` |
| 4, 21 (also discussed on 14) | Baseline balance permutation p-values | `balance_permutation.csv` |

Repeated narrative estimates elsewhere reuse these rows. The slide companion report explains how each table and figure is assembled, with denominators, units, interpretation and limitations.

## Equations and treatment definitions

The equations printed above the regression tables describe the models already implemented below; adding their notation does not change an estimate. Let `Z = selected`, `D = in_private_now`, and `M = male`.

- Pooled offer effects: `Y = alpha + tau Z + error`. First stage: `D = a + pi Z + error`.
- Age-specific offer effects: `Y = alpha_g + tau_g Z + error` within baseline-age group `g`; the direct equality test compares the three `tau_g` values.
- Sex effects: `Y = alpha + tau Z + gamma M + delta (Z × M) + error`. Girls: `tau`; boys: `tau + delta`; boys-minus-girls: `delta`. Use the interaction test, not a comparison of subgroup p-values.
- Interacted adjustment: `Y = alpha + tau Z + X_centered' gamma + (Z × X_centered)' delta + error`. Targeted exclusions use the simpler offer model on the named restricted sample.
- Additive fixed effects: `Y = alpha + tau Z + X' gamma + SES effects + neighborhood effects + error`, with the specific baseline coding explained in chunk 12.
- IV: first stage `D = a + pi Z + W' gamma + v`; structural outcome `Y = b + beta D + W' theta + u`, instrumenting `D` with `Z`. Reduced form `Y = c + rho Z + W' eta + e`. Just-identified `beta_IV = rho / pi`. The same exogenous controls `W` and common observed sample enter both regressions. `W` is omitted for the main unadjusted IV, uses the earlier baseline controls in its sensitivity, and includes the categorical fixed effects in the controlled IV.

**ATT now refers to private schooling:** `ATT_D = E[Y(1) - Y(0) | D = 1]`, with potential outcomes indexed by private attendance. Lottery selection is the subsidy offer. `D(1)` denotes attendance if offered and `D(0)` attendance without an offer. Under the IV assumptions, the ratio identifies a complier effect, `E[Y(1) - Y(0) | D(1) > D(0)]`. Controls' private attendance of about 53.8% rules out one-sided schooling uptake. Observed private attenders include always-attenders as well as offer-induced attenders, and the always-attenders' treatment effects are not identified by the lottery. Thus no separate all-attender ATT is calculated. One-sided uptake with `D(0) = 0` (contradicted here), or an additional equal-mean-effect assumption across always-attenders and compliers, would bridge the estimands under the remaining IV assumptions. Current-aid rates are no longer generated in this focused analysis.

## How to run

Use **base R**, with no extra R packages. The package must contain `data/raw/study_baseline.csv` and `data/raw/study_followup.csv`.

For interactive execution, set R's working directory to the package folder containing `data/`, `code/` and `results/`, then run the **14 R chunks** below in order. Alternatively, the accompanying executable contains the exact same code:

```sh
Rscript code/slide_regressions.R
```

The script regenerates 17 CSV files under `results/slide_regressions/` and preserves the raw data. Binary effects are proportions in CSVs: multiply by 100 for percentage points in the slides. Binary arm means become percentages after multiplication by 100. School years, grades, repetition counts and weekly hours retain their original units.

**Inference:** offer, subgroup and sensitivity p-values use two-sided HC2/t tests. Age-effect equality tests use a joint HC2/F test. IV tables label the zero-effect AR p-value to match their AR confidence sets; this differs from a conventional IV Wald p-value. Holm columns identify the stated multiple-testing families. Unavailable p-values for zero-event outcomes do not equal zero or one. Slides show p-values to three decimals, with values below 0.001 written `<.001`. Ordinary 95% intervals are pointwise, not simultaneous. Exploratory subgroup comparisons warrant caution.

## 1. Read the data and define the two sensitivity flags

Read the original baseline and follow-up CSVs and join them by applicant ID. The checks stop execution if IDs are missing, duplicated or unmatched. Cohorts remain separate. A2020 is the primary sample.

Only two record flags are needed for the displayed sensitivity regressions: decreasing age and reporting no work with positive hours. Both flags require the relevant fields to be observed. Original values remain unchanged. The flags cause exclusions only in the explicitly named sensitivity models; neither changes the main sample.

```r
#!/usr/bin/env Rscript
# Reproduce only the results displayed in the current slide deck.
# Base R only. Run: Rscript code/slide_regressions.R

# CHUNK 1: Read the original files and prepare the displayed analysis samples.
options(stringsAsFactors=FALSE)
cmd <- commandArgs(trailingOnly=FALSE)
file_arg <- sub("^--file=", "", cmd[grepl("^--file=",cmd)])
root <- if(length(file_arg)) dirname(dirname(normalizePath(file_arg))) else normalizePath(".")
out <- file.path(root,"results/slide_regressions")
dir.create(out,recursive=TRUE,showWarnings=FALSE)
b <- read.csv(file.path(root,"data/raw/study_baseline.csv"),na.strings=c("","NA"))
f <- read.csv(file.path(root,"data/raw/study_followup.csv"),na.strings=c("","NA"))
stopifnot(!anyNA(b$applicant_id),!anyNA(f$applicant_id),!anyDuplicated(b$applicant_id),!anyDuplicated(f$applicant_id),setequal(b$applicant_id,f$applicant_id))
d <- merge(b,f,by="applicant_id",sort=TRUE)
d$cohort <- paste(d$municipality,d$application_year,sep="_")
policy <- c("years_in_school","married_or_cohab","has_child","working","hours_worked")
school <- c("in_school_now","in_private_now","highest_grade","total_repeats")
a20 <- d[d$cohort=="A_2020",]
a20$age_decreased <- with(a20,!is.na(age_at_application)&!is.na(age_at_survey)&age_at_survey<age_at_application)
a20$work_conflict <- with(a20,!is.na(working)&!is.na(hours_worked)&working==0&hours_worked>0)
save_table <- function(x,name) write.csv(x,file.path(out,paste0(name,".csv")),row.names=FALSE,na="")

```

## 2. Calculate HC2 standard errors and regression p-values

`fit_hc2()` fits the stated linear regression and computes applicant-level heteroskedasticity-robust HC2 covariance. HC2 divides squared residuals by one minus regression leverage. The contrast helper calculates an estimate, its standard error, an ordinary 95% t interval and a two-sided p-value using the model's residual degrees of freedom.

`offer_fit()` estimates `Y ~ selected` on applicants with that outcome observed. The coefficient on `selected` equals the treatment-group mean minus the control-group mean. The means and arm counts use that exact outcome sample. Extending an observed-response contrast to all randomized applicants requires suitable response assumptions; outcome-specific omission does not itself remove missing-data bias. The entire A2022 sample and the youngest A2020 age group have zero observed marriage and parenthood events. Their descriptive means and zero differences remain available, but degenerate robust intervals and p-values are suppressed. This does not establish no effect in the population.

```r
# CHUNK 2: Define OLS with applicant-level HC2 covariance and t tests.
fit_hc2 <- function(formula,data) {
  fit <- lm(formula,data=data,na.action=na.omit)
  co <- coef(fit); keep <- !is.na(co); co <- co[keep]
  X <- model.matrix(fit)[,keep,drop=FALSE]
  B <- solve(crossprod(X)); h <- rowSums((X%*%B)*X)
  w <- as.numeric(residuals(fit)^2/pmax(1-h,1e-10))
  V <- B%*%crossprod(X,X*w)%*%B
  dimnames(V) <- list(names(co),names(co))
  list(coef=co,V=V,n=nrow(X),df=fit$df.residual,rank=ncol(X),max_leverage=max(h),
       aliased=paste(names(coef(fit))[!keep],collapse=", "))
}
linear_effect <- function(fit,terms) {
  L <- setNames(rep(0,length(fit$coef)),names(fit$coef))
  L[names(terms)] <- terms
  estimate <- sum(L*fit$coef)
  se <- sqrt(max(0,as.numeric(t(L)%*%fit$V%*%L)))
  crit <- qt(.975,fit$df)
  data.frame(estimate=estimate,se=se,ci_low=estimate-crit*se,ci_high=estimate+crit*se,
    p_value=if(se>0) 2*pt(-abs(estimate/se),fit$df) else NA_real_,n=fit$n,df=fit$df)
}
offer_fit <- function(x,y) {
  x <- x[!is.na(x[[y]]),]
  fit <- fit_hc2(as.formula(paste(y,"~ selected")),x)
  r <- linear_effect(fit,c(selected=1))
  r$cohort <- x$cohort[1]; r$outcome <- y
  r$control_mean <- mean(x[x$selected==0,y]); r$treatment_mean <- mean(x[x$selected==1,y])
  r$n_control <- sum(x$selected==0); r$n_treatment <- sum(x$selected==1)
  r$inference_status <- "HC2/t"
  if(length(unique(x[[y]]))<2) {
    r[,c("se","ci_low","ci_high","p_value")] <- NA_real_
    r$inference_status <- "Not reported: no observed outcome variation"
  }
  r
}

```

## 3. Estimate the displayed offer effects — slides 5, 6 and 14

Fit the five policy outcomes and four schooling outcomes in A2020. In A2022 and B2018, fit the five policy outcomes plus current private attendance needed for slide 9. This is exactly 21 unique cohort/outcome comparisons; repeated values across slides reuse the same row.

The displayed raw p-values test a zero offer effect. Holm correction covers the five policy outcomes separately within each cohort, and the four schooling outcomes in A2020. The code also reproduces the combined-nine A2020 correction discussed in the notes. It keeps the full family size when a zero-event p-value is unavailable. A2022/B2018 private-attendance rows show raw p-values only: computing a four-outcome schooling correction there would require undisplayed regressions.

**Output:** `itt.csv`.

```r
# CHUNK 3: Slides 5, 6 and 14: exactly the displayed offer-effect models.
itt_rows <- list()
for(cohort in c("A_2020","A_2022","B_2018")) {
  outcomes <- if(cohort=="A_2020") c(policy,school) else c(policy,"in_private_now")
  for(y in outcomes) itt_rows[[length(itt_rows)+1]] <- offer_fit(d[d$cohort==cohort,],y)
}
itt <- do.call(rbind,itt_rows)
itt$holm_p <- NA_real_; itt$holm_all_nine_p <- NA_real_
for(cohort in c("A_2020","A_2022","B_2018")) {
  ix <- itt$cohort==cohort&itt$outcome%in%policy
  itt$holm_p[ix] <- p.adjust(itt$p_value[ix],"holm",n=5)
}
ix <- itt$cohort=="A_2020"&itt$outcome%in%school
itt$holm_p[ix] <- p.adjust(itt$p_value[ix],"holm",n=4)
ix <- itt$cohort=="A_2020"
itt$holm_all_nine_p[ix] <- p.adjust(itt$p_value[ix],"holm",n=9)
save_table(itt,"itt")

```

## 4. Reuse the first-stage regressions — slide 9

The offer effect on current private attendance is also the IV first stage. This chunk reuses its three rows from the previous table instead of fitting extra regressions. These rows provide the control and treatment shares for the chart, the first-stage difference, 95% interval and raw p-value.

With one excluded instrument, the robust first-stage F statistic equals the square of the HC2 t statistic. These rows use all observed private-school responses. The IV models below use a common outcome/private-status sample, so their first stages can differ slightly.

**Output:** `first_stages.csv`.

```r
# CHUNK 4: Slide 9: reuse the three displayed current-private first stages.
first_stages <- itt[itt$outcome=="in_private_now",]
first_stages$F_statistic <- (first_stages$estimate/first_stages$se)^2
save_table(first_stages,"first_stages")

```

## 5. Prepare the baseline controls used in the displayed checks

Within the full A2020 cohort, replace missing baseline age and SES with their respective observed means and add missingness indicators. Keep original source columns. Controls also include sex and whether the application recorded a phone number. Constant controls are dropped; phone is constant in A2020.

The means used for imputation and centering come from all randomized A2020 applicants before outcome-specific omissions. They do not depend on outcomes or lottery arm. Centering makes the assignment coefficient in the following interacted model the effect evaluated at that fixed baseline covariate profile. The additive IV adjustment later uses the uncentered controls, an equivalent location shift with an intercept.

```r
# CHUNK 5: Prepare baseline controls needed by slides 18, 19, 23 and 24.
for(v in c("age_at_application","ses_stratum")) {
  a20[[paste0(v,"_missing")]] <- as.integer(is.na(a20[[v]]))
  a20[[paste0(v,"_imp")]] <- a20[[v]]
  a20[[paste0(v,"_imp")]][is.na(a20[[v]])] <- mean(a20[[v]],na.rm=TRUE)
}
controls <- c("male","has_phone","age_at_application_imp","age_at_application_missing","ses_stratum_imp","ses_stratum_missing")
controls <- controls[vapply(a20[controls],function(x) length(unique(x))>1,logical(1))]
centered <- paste0(controls,"_centered")
for(i in seq_along(controls)) a20[[centered[i]]] <- a20[[controls[i]]]-mean(a20[[controls[i]]])

```

## 6. Estimate the displayed policy sensitivities — slide 18

For each of the five policy outcomes, fit three additional models: exclude the declining-age case, exclude the work-hours conflict, and adjust for baseline covariates with assignment interactions. The “Primary” column on the slide reuses the earlier unadjusted ITT rather than fitting it again. There are exactly 15 additional models.

The adjusted formula is `Y ~ selected * (centered baseline controls)`. Its `selected` coefficient and HC2 p-value are the displayed adjusted effect and test. Raw treatment/control means do not subtract to this adjusted coefficient, so those mean fields are left blank. Exclusions apply to every displayed outcome in the corresponding column; missing outcomes still remain missing. These sensitivity p-values are raw, and the specifications are not separate confirmatory discoveries.

**Output:** `policy_sensitivity.csv`.

```r
# CHUNK 6: Slide 18: three displayed sensitivities for each policy outcome.
sensitivity_rows <- list()
for(y in policy) {
  samples <- list("Exclude declining-age records"=a20[!a20$age_decreased,],
                  "Exclude work-hours contradiction"=a20[!a20$work_conflict,])
  for(spec in names(samples)) {
    r <- offer_fit(samples[[spec]],y); r$specification <- spec
    sensitivity_rows[[length(sensitivity_rows)+1]] <- r
  }
  formula <- as.formula(paste(y,"~ selected * (",paste(centered,collapse=" + "),")"))
  fit <- fit_hc2(formula,a20)
  r <- linear_effect(fit,c(selected=1)); r$cohort <- "A_2020"; r$outcome <- y
  # The coefficient is a covariate-adjusted contrast; raw arm means are not it.
  r$control_mean <- r$treatment_mean <- NA_real_
  r$n_control <- sum(a20$selected==0&!is.na(a20[[y]]))
  r$n_treatment <- sum(a20$selected==1&!is.na(a20[[y]]))
  r$inference_status <- "HC2/t"
  r$specification <- "Baseline adjustment with assignment interactions"
  sensitivity_rows[[length(sensitivity_rows)+1]] <- r
}
policy_sensitivity <- do.call(rbind,sensitivity_rows)
save_table(policy_sensitivity,"policy_sensitivity")

```

## 7. Define the confidence-set calculation used by the IV slides

An AR-type test of a candidate effect `b` tests whether the lottery coefficient in `Y - bD` is zero. Accept `b` when `(RF - b FS)^2` is no larger than the squared t critical value times its HC2 variance. Expanding this condition gives a quadratic inequality.

The helper solves that inequality, retaining bounded, disjoint or unbounded confidence sets instead of forcing every answer into a finite interval. The displayed A2020 sets are bounded. This is approximate heteroskedasticity-robust inference using a t reference; it does not resolve exclusion or monotonicity concerns.

```r
# CHUNK 7: Define the robust AR confidence-set inversion used on IV slides.
ar_set <- function(A,B,C) {
  if(abs(A)<1e-12) {
    if(abs(B)<1e-12) return(list(type=if(C<=0) "all real" else "empty",low=NA_real_,high=NA_real_,text=if(C<=0) "All real numbers" else "Empty set"))
    r <- -C/B
    return(list(type="half-line",low=if(B>0) -Inf else r,high=if(B>0) r else Inf,
      text=if(B>0) sprintf("(-Inf, %.6f]",r) else sprintf("[%.6f, Inf)",r)))
  }
  discriminant <- B^2-4*A*C
  if(discriminant<0) return(list(type=if(A<0) "all real" else "empty",low=NA_real_,high=NA_real_,text=if(A<0) "All real numbers" else "Empty set"))
  endpoints <- sort(c((-B-sqrt(discriminant))/(2*A),(-B+sqrt(discriminant))/(2*A)))
  list(type=if(A>0) "bounded" else "disjoint",low=endpoints[1],high=endpoints[2],
    text=if(A>0) sprintf("[%.6f, %.6f]",endpoints[1],endpoints[2]) else sprintf("(-Inf, %.6f] U [%.6f, Inf)",endpoints[1],endpoints[2]))
}

```

## 8. Define the matched-sample IV estimator

For one displayed specification, retain only applicants observed on the outcome, the chosen private-school measure and lottery assignment. Fit the outcome reduced form and the private-school first stage using the same design matrix and the same rows. The just-identified IV coefficient is `RF / FS`.

The joint HC2 covariance retains covariance between RF and FS. It supplies the AR set and the AR p-value for a zero effect shown on the slides. The first-stage F and its own two-sided p-value are also saved. The adjusted specifications add the same baseline controls to both equations. The fixed-effects version replaces the earlier numeric SES adjustment with categorical SES indicators and adds categorical neighborhood indicators, retaining baseline sex, phone, age and age missingness. Both equations use this same design. Redundant columns, including constant phone status, are removed by the design-matrix rank calculation. These IV adjustments are additive, unlike the assignment-interacted policy adjustment above.

Here the instrument is lottery assignment, not current aid receipt. Private schooling is endogenous. Interpreting the ratio as a complier effect requires the stated IV assumptions; a current attendance indicator may not capture earlier schooling or direct financial effects of the subsidy.

```r
# CHUNK 8: Fit one IV specification on a common outcome/private-status sample.
iv_fit <- function(y,exposure="in_private_now",adjusted=FALSE,fixed_effects=FALSE) {
  x <- a20[complete.cases(a20[,c(y,exposure,"selected")]),]
  X <- cbind(intercept=1,selected=x$selected)
  if(fixed_effects) X <- model.matrix(fe_rhs,x) else if(adjusted) X <- cbind(X,as.matrix(x[controls]))
  q <- qr(X); X <- X[,q$pivot[seq_len(q$rank)],drop=FALSE]
  fit <- lm.fit(X,cbind(Y=x[[y]],D=x[[exposure]]))
  B <- solve(crossprod(X)); h <- rowSums((X%*%B)*X)
  influence <- (X%*%B)[,"selected"]/sqrt(pmax(1-h,1e-10))
  V <- crossprod(fit$residuals*as.numeric(influence))
  rf <- unname(fit$coefficients["selected","Y"]); fs <- unname(fit$coefficients["selected","D"])
  estimate <- rf/fs; n <- nrow(X); df <- n-ncol(X); crit <- qt(.975,df)
  conf <- ar_set(fs^2-crit^2*V[2,2],-2*rf*fs+2*crit^2*V[1,2],rf^2-crit^2*V[1,1])
  data.frame(cohort="A_2020",outcome=y,exposure=exposure,baseline_adjusted=adjusted,
    estimate=estimate,ar_p_zero=2*pt(-abs(rf/sqrt(V[1,1])),df),ar_type=conf$type,
    ar_low=conf$low,ar_high=conf$high,ar_set=conf$text,reduced_form=rf,first_stage=fs,
    first_stage_se=sqrt(V[2,2]),first_stage_F=fs^2/V[2,2],first_stage_p=2*pt(-abs(fs/sqrt(V[2,2])),df),
    n=n,n_control=sum(x$selected==0),n_treatment=sum(x$selected==1),df=df)
}

```

## 9. Estimate exactly the displayed IV specifications — slides 12 and 19

Slide 12 shows five A2020 IV estimates using current private attendance and no baseline adjustment. Slide 19 reuses its weekly-hours row and adds three weekly-hours specifications: current attendance with additive baseline adjustment, private G6 entry, and private G7 entry. This yields eight unique IV specifications.

The five main AR p-values receive the five-outcome Holm correction discussed on slide 12. The three hours-only alternatives have raw AR p-values. The code does not fit the other outcomes under those alternative specifications merely to calculate an undisplayed correction.

**Output:** `iv.csv`.

```r
# CHUNK 9: Slides 12 and 19: five main IV effects and three hours alternatives.
iv <- do.call(rbind,lapply(policy,iv_fit))
iv$holm_ar_p <- p.adjust(iv$ar_p_zero,"holm",n=5)
extra <- rbind(iv_fit("hours_worked",adjusted=TRUE),
               iv_fit("hours_worked",exposure="started_g6_private"),
               iv_fit("hours_worked",exposure="started_g7_private"))
# Other outcomes under these alternative specifications are not displayed or fit.
extra$holm_ar_p <- NA_real_
iv <- rbind(iv,extra)
save_table(iv,"iv")

```

## 10. Estimate sex-specific effects and their differences — slides 7 and 20

For each of the nine A2020 outcomes, fit `Y ~ selected * male`. Girls' effect is the `selected` coefficient. Boys' effect adds the `selected:male` coefficient. The interaction alone directly tests boys minus girls. These nine fitted models produce the 27 displayed estimates and their raw p-values. The dedicated main slide reuses the four schooling outcomes; the appendix retains all nine outcomes. No new regressions are needed for the main discussion.

All three contrasts use the same four-cell model and its full residual degrees of freedom. The two subgroup p-values test their own effects; the difference p-value tests whether those effects differ. Holm adjustment applies to the five policy interaction tests and separately to the four schooling interaction tests. A difference in subgroup significance is not a test of effect heterogeneity.

**Output:** `sex.csv`. The checks confirm the expected row counts for these five regression outputs. Later chunks add the application-age and fixed-effects results and the descriptive evidence displayed in the deck.

```r
# CHUNK 10: Slides 7 and 20: girls, boys and their directly tested effect difference.
sex_rows <- list()
for(y in c(policy,school)) {
  fit <- fit_hc2(as.formula(paste(y,"~ selected * male")),a20)
  for(group in c("Girls","Boys","Boys minus girls")) {
    terms <- switch(group,"Girls"=c(selected=1),"Boys"=c(selected=1,"selected:male"=1),
                    "Boys minus girls"=c("selected:male"=1))
    r <- linear_effect(fit,terms); r$cohort <- "A_2020"; r$outcome <- y; r$sex <- group
    r$subgroup_n <- sum(!is.na(a20[[y]]) & if(group=="Boys minus girls") TRUE else a20$male==as.integer(group=="Boys"))
    sex_rows[[length(sex_rows)+1]] <- r
  }
}
sex <- do.call(rbind,sex_rows); sex$holm_interaction_p <- NA_real_
for(outcomes in list(policy,school)) {
  ix <- sex$sex=="Boys minus girls"&sex$outcome%in%outcomes
  sex$holm_interaction_p[ix] <- p.adjust(sex$p_value[ix],"holm",n=length(outcomes))
}
save_table(sex,"sex")
stopifnot(nrow(itt)==21,nrow(first_stages)==3,nrow(policy_sensitivity)==15,nrow(iv)==8,nrow(sex)==27)

```

## 11. Estimate effects within application-age groups — slides 8 and 22

Use only age recorded on the application to form the user-selected groups 10–11, 12–13 and 14–18. They contain 215, 634 and 271 applicants, respectively. The 56 applicants with missing application age remain in the primary pooled-across-ages A2020 analysis and the controlled models; they cannot be assigned to these age groups. These are not verified grade groups. The data have no baseline-grade field, and follow-up grade is potentially affected by the offer. Recorded baseline ages are retained even when an age pair is inconsistent: ID 100368 reports application age 15 and survey age 10, so it remains in ages 14–18. The data cannot establish which age is wrong; we do not guess a correction. The displayed pooled exclusion check addresses that record, while measurement error can still blur age-group comparisons.

For each of the nine outcomes, fit `Y ~ selected` separately within each age group, with outcome-specific missingness. Each effect uses its own group/sample HC2 covariance and t reference with `n_group - 2` degrees of freedom. Save arm means, arm counts and binary event counts for transparent interpretation. There are 27 group-specific estimates. No age-specific IV models are fitted.

Directly test equality of the three offer effects. Let `tau = (tau_10–11, tau_12–13, tau_14–18)` and let `L` compare each older group to the youngest. The two-restriction Wald statistic is `(L tau)' [L V L']^(-1) (L tau) / 2`, where `V` is diagonal because the groups are disjoint. Use an F reference with 2 numerator degrees of freedom and `N_observed_age_and_outcome - 6` denominator degrees of freedom. This matches a saturated age-by-assignment HC2 interaction test. It tests differences directly; different within-group p-values do not establish heterogeneous effects.

Marriage and parenthood have no observed events in the youngest group. Report the observed zero contrasts but suppress their within-group intervals/p-values and the corresponding joint age tests. Apply Holm to the five policy equality tests and separately to the four schooling equality tests, retaining the stated family sizes when p-values are unavailable. Within-group p-values are unadjusted and exploratory.

**Outputs:** `age_groups.csv`, `age_effects.csv`, `age_heterogeneity.csv`.

```r
# CHUNK 11: Separate A2020 by pre-assignment application-age groups.
# These are age groups, not verified grades. Unknown ages stay in the main ITT.
age_levels <- c("10-11","12-13","14-18")
a20$age_group <- cut(a20$age_at_application,breaks=c(9,11,13,18),labels=age_levels)
stopifnot(all(is.na(a20$age_at_application)|!is.na(a20$age_group)))
age_counts <- do.call(rbind,lapply(c(age_levels,"Missing"),function(g) {
  x <- a20[if(g=="Missing") is.na(a20$age_group) else !is.na(a20$age_group)&a20$age_group==g,]
  data.frame(age_group=g,n=nrow(x),n_control=sum(x$selected==0),n_treatment=sum(x$selected==1))
}))
save_table(age_counts,"age_groups")
age_rows <- list()
for(y in c(policy,school)) for(g in age_levels) {
  x <- a20[!is.na(a20$age_group)&a20$age_group==g,]
  r <- offer_fit(x,y); r$age_group <- g
  r$events_control <- if(y%in%c("married_or_cohab","has_child","working","in_school_now","in_private_now")) sum(x[x$selected==0,y],na.rm=TRUE) else NA_real_
  r$events_treatment <- if(y%in%c("married_or_cohab","has_child","working","in_school_now","in_private_now")) sum(x[x$selected==1,y],na.rm=TRUE) else NA_real_
  age_rows[[length(age_rows)+1]] <- r
}
age_effects <- do.call(rbind,age_rows)
save_table(age_effects,"age_effects")
# Direct equality test: the independent age-cell effects have diagonal HC2 V.
# This equals the two-interaction Wald test in a saturated age x assignment model.
age_tests <- do.call(rbind,lapply(c(policy,school),function(y) {
  rr <- age_effects[age_effects$outcome==y,]; tau <- rr$estimate
  L <- rbind(c(-1,1,0),c(-1,0,1)); denom_df <- sum(rr$n)-6
  V <- L%*%diag(rr$se^2)%*%t(L); delta <- L%*%tau
  available <- all(is.finite(V)) && qr(V)$rank==2
  stat <- if(available) as.numeric(t(delta)%*%solve(V,delta))/2 else NA_real_
  data.frame(outcome=y,F_statistic=stat,numerator_df=2,denominator_df=denom_df,n=sum(rr$n),
    p_value=if(available) pf(stat,2,denom_df,lower.tail=FALSE) else NA_real_,
    inference_status=if(available) "HC2/F test of equal age-group offer effects" else "Not reported: constant outcome in at least one age group")
}))
age_tests$holm_p <- NA_real_
for(outcomes in list(policy,school)) {
  ix <- age_tests$outcome%in%outcomes
  age_tests$holm_p[ix] <- p.adjust(age_tests$p_value[ix],"holm",n=length(outcomes))
}
save_table(age_tests,"age_heterogeneity")

```

## 12. Add baseline controls and categorical fixed effects — slides 23 and 24

Keep pooled-across-ages A2020 as the sample. The adjusted offer regression is:

`Y ~ selected + male + has_phone + age_at_application_imp + age_at_application_missing + ses_category + neighborhood_category`

SES and neighborhood enter as separate categorical fixed effects, not their numeric codes and not a joint SES-by-neighborhood interaction. Each has an explicit `Missing` level. Baseline age uses the full-cohort observed mean plus a missingness indicator prepared in chunk 5. Thus missing controls do not remove applicants; only a missing outcome removes a row from an offer regression. No follow-up variable is a control. Every A2020 applicant has `has_phone = 1`, so it is specified but aliased with the intercept and cannot have a separately estimated coefficient. The fitted matrices have rank 26. The category-count table documents the exact coding and sparse cells.

Fit all nine displayed outcomes with applicant-level HC2 covariance and t reference with `n - rank` degrees of freedom. Fixed effects do not imply clustered standard errors. The selected coefficient is an adjusted contrast, not the raw difference between treatment and control group means. Apply Holm separately to the five policy and four schooling coefficients.

For the five controlled IV models, use current private attendance as the exposure and lottery selection as the instrument. Use the exact same covariates and categorical fixed effects in both reduced form and first stage, on a common observed outcome/exposure sample. Reuse the ratio, joint-HC2 AR confidence-set and first-stage calculations from chunk 8. Adjust the five AR p-values with Holm. These controls can improve precision under their assumptions; they do not remove bias from unobserved outcomes or establish the IV exclusion restriction. These are additional sensitivity specifications, distinct from the earlier interacted adjustment with mean-imputed numeric SES.

**Outputs:** `fe_itt.csv`, `fe_iv.csv`, `fe_category_counts.csv`.

```r
# CHUNK 12: Add baseline controls and separate SES/neighborhood fixed effects.
# Missing categories preserve respondents; no post-assignment controls are used.
a20$ses_category <- factor(ifelse(is.na(a20$ses_stratum),"Missing",as.character(a20$ses_stratum)))
a20$neighborhood_category <- factor(ifelse(is.na(a20$neighborhood),"Missing",as.character(a20$neighborhood)))
fe_rhs <- ~ selected + male + has_phone + age_at_application_imp + age_at_application_missing + ses_category + neighborhood_category
fe_itt <- do.call(rbind,lapply(c(policy,school),function(y) {
  formula <- update(fe_rhs,as.formula(paste(y,"~ .")))
  fit <- fit_hc2(formula,a20)
  r <- linear_effect(fit,c(selected=1)); r$outcome <- y; r$cohort <- "A_2020"
  r$n_control <- sum(a20$selected==0&!is.na(a20[[y]])); r$n_treatment <- sum(a20$selected==1&!is.na(a20[[y]]))
  r$rank <- fit$rank; r$max_leverage <- fit$max_leverage; r$aliased <- fit$aliased
  r$specification <- "Additive baseline controls plus SES and neighborhood fixed effects"
  r
}))
fe_itt$holm_p <- NA_real_
for(outcomes in list(policy,school)) {
  ix <- fe_itt$outcome%in%outcomes
  fe_itt$holm_p[ix] <- p.adjust(fe_itt$p_value[ix],"holm",n=length(outcomes))
}
save_table(fe_itt,"fe_itt")
fe_iv <- do.call(rbind,lapply(policy,function(y) iv_fit(y,adjusted=TRUE,fixed_effects=TRUE)))
fe_iv$holm_ar_p <- p.adjust(fe_iv$ar_p_zero,"holm",n=5)
fe_iv$specification <- "Additive baseline controls plus SES and neighborhood fixed effects"
save_table(fe_iv,"fe_iv")
fe_levels <- do.call(rbind,lapply(c("ses_category","neighborhood_category"),function(v) {
  do.call(rbind,lapply(levels(a20[[v]]),function(level) {
    x <- a20[a20[[v]]==level,]
    data.frame(variable=v,level=level,n=nrow(x),n_control=sum(x$selected==0),n_treatment=sum(x$selected==1))
  }))
}))
save_table(fe_levels,"fe_category_counts")

```

## 13. Reproduce the displayed data checks and descriptive tables

Count cohort sizes and assignment arms from the matched raw records. Compute age change only when both ages are observed. A negative change is a chronological contradiction; a change outside 2–4 years is a review flag relative to the stated approximate three-year horizon. Neither automatically deletes or corrects a record. The cohort-specific age-change summaries reveal why a universal three-year assumption needs clarification.

Flag a grade contradiction when any observed `finished_g6`, `finished_g7` or `finished_g8` disagrees with the corresponding threshold of observed `highest_grade`. Count each applicant once. Flag nonworkers reporting positive hours, retain workers reporting zero hours, and flag reported school years above four without treating an uncertain timing screen as a verified error. The six example IDs are the records displayed in the appendix; save their original fields verbatim.

For the observed-exit table, restrict each cohort/arm to reported G6 private entrants with observed current private status. Count an exit when current private status equals zero. Exclude unknown current statuses from the denominator and report them separately. Split observed exits by current enrollment where observed. G6 private entry occurs after assignment; these transitions are descriptive and do not identify causal defiers or switching caused by the offer.

Count missing values for the five primary outcomes over all 1,176 A2020 applicants. The counterfactual-credibility discussion reuses these counts, cohort assignment totals and the balance check. Missing private status by arm is the cohort arm total minus the observed arm count in the private-attendance ITT. The ATT discussion reuses private-attendance means from the first stage; it does not treat current aid receipt as the treatment or instrument. The comprehensive record audit remains in the separate full-analysis files.

**Outputs:** `cohort_summary.csv`, `audit_counts.csv`, `transitions.csv`, `record_examples.csv`, `policy_missingness.csv`.

```r
# CHUNK 13: Produce only the descriptive evidence displayed in the deck.
d$age_change <- d$age_at_survey-d$age_at_application
d$age_decreased <- !is.na(d$age_change)&d$age_change<0
d$age_off_window <- !is.na(d$age_change)&(d$age_change<2|d$age_change>4)
d$grade_conflict <- FALSE
for(g in 6:8) {
  value <- d[[paste0("finished_g",g)]]
  d$grade_conflict <- d$grade_conflict|(!is.na(value)&!is.na(d$highest_grade)&value!=as.integer(d$highest_grade>=g))
}
d$work_conflict <- with(d,!is.na(working)&!is.na(hours_worked)&working==0&hours_worked>0)
cohort_summary <- do.call(rbind,lapply(c("A_2020","A_2022","B_2018"),function(cohort) {
  x <- d[d$cohort==cohort,]
  data.frame(cohort=cohort,n=nrow(x),selected=sum(x$selected),control=sum(x$selected==0),
    age_pairs=sum(!is.na(x$age_change)),mean_age_change=mean(x$age_change,na.rm=TRUE),median_age_change=median(x$age_change,na.rm=TRUE),
    age_decreased=sum(x$age_decreased),age_outside_2_to_4=sum(x$age_off_window),age_missing=sum(is.na(x$age_change)))
}))
save_table(cohort_summary,"cohort_summary")
audit_counts <- data.frame(metric=c("matched_unique_ids","age_decreased","age_outside_2_to_4","grade_conflict","no_work_positive_hours","working_zero_hours","school_years_above_four"),
 count=c(nrow(d),sum(d$age_decreased),sum(d$age_off_window),sum(d$grade_conflict),sum(d$work_conflict),sum(d$working==1&d$hours_worked==0,na.rm=TRUE),sum(d$years_in_school>4,na.rm=TRUE)))
save_table(audit_counts,"audit_counts")
transitions <- list()
for(cohort in c("A_2020","A_2022","B_2018")) for(z in 0:1) {
  x <- d[d$cohort==cohort&d$selected==z,]
  base <- !is.na(x$started_g6_private)&x$started_g6_private==1
  paired <- base&!is.na(x$in_private_now); exits <- paired&x$in_private_now==0
  transitions[[length(transitions)+1]] <- data.frame(cohort=cohort,selected=z,prior_private=sum(base),paired_observed=sum(paired),
    later_unknown=sum(base&is.na(x$in_private_now)),exits=sum(exits),exit_fraction=sum(exits)/sum(paired),
    exits_currently_enrolled=sum(exits&x$in_school_now==1,na.rm=TRUE),exits_not_currently_enrolled=sum(exits&x$in_school_now==0,na.rm=TRUE))
}
save_table(do.call(rbind,transitions),"transitions")
example_ids <- c(100368,100044,100203,100767,100031,100062)
example_columns <- c("applicant_id","cohort","selected","age_at_application","age_at_survey","highest_grade","finished_g6","finished_g7","finished_g8","working","hours_worked","started_g6_private","started_g7_private","in_private_now","in_school_now")
save_table(d[match(example_ids,d$applicant_id),example_columns],"record_examples")
missing <- data.frame(outcome=policy,n=nrow(a20),missing=vapply(a20[policy],function(x) sum(is.na(x)),integer(1)))
save_table(missing,"policy_missingness")

```

## 14. Reproduce the displayed baseline-balance check — slides 4 and 21

Within each cohort, use baseline sex, recorded phone, mean-imputed age and numeric SES, plus missingness indicators; drop constant columns. Center this fixed covariate matrix and use its full-cohort covariance. The Mahalanobis statistic summarizes the assignment-arm difference across these baseline variables.

With seed `20260922`, draw 9,999 random reassignments within each cohort while fixing its observed selected count. The p-value is `(1 + number of simulated statistics at least as large as observed) / 10,000`; the one-added convention avoids a spurious zero Monte Carlo p-value. Save its Monte Carlo standard error as well. This conditional randomization check is distinct from the regression/AR inference used for effects and assumes the stated applicant-level lottery. Its p-values neither prove valid randomization nor show that adjustment repairs an invalid lottery.

The main counterfactual slide reuses the A2020 balance p-value; the methods appendix retains all three cohorts. Balance nonrejection is consistent with the lottery account but does not prove that the comparison is valid, establish no spillovers or remove bias from missing responses. No undisplayed regressions are needed. The concluding checks verify expected age-group and controlled-model counts.

**Output:** `balance_permutation.csv`.

```r
# CHUNK 14: Reproduce the balance p-values displayed in the methods appendix.
# This is a nonregression randomization check, included because it is on the slide.
set.seed(20260922); permutations <- 9999L
balance <- do.call(rbind,lapply(c("A_2020","A_2022","B_2018"),function(cohort) {
  x <- d[d$cohort==cohort,]
  for(v in c("age_at_application","ses_stratum")) {
    x[[paste0(v,"_missing")]] <- as.integer(is.na(x[[v]]))
    x[[paste0(v,"_imp")]] <- ifelse(is.na(x[[v]]),mean(x[[v]],na.rm=TRUE),x[[v]])
  }
  cc <- c("male","has_phone","age_at_application_imp","age_at_application_missing","ses_stratum_imp","ses_stratum_missing")
  cc <- cc[vapply(x[cc],function(v) length(unique(v))>1,logical(1))]
  X <- scale(as.matrix(x[cc]),center=TRUE,scale=FALSE)
  n <- nrow(x); n1 <- sum(x$selected); n0 <- n-n1
  inverse <- solve((1/n1+1/n0)*cov(X))
  statistic <- function(ids) {
    difference <- colSums(X[ids,,drop=FALSE])*(1/n1+1/n0)
    as.numeric(t(difference)%*%inverse%*%difference)
  }
  observed <- statistic(which(x$selected==1))
  simulated <- replicate(permutations,statistic(sample.int(n,n1,replace=FALSE)))
  p <- (1+sum(simulated>=observed-1e-12))/(permutations+1)
  data.frame(cohort=cohort,n=n,n_selected=n1,n_control=n0,mahalanobis_statistic=observed,permutations=permutations,p_value=p,
    monte_carlo_se=sqrt(p*(1-p)/(permutations+1)))
}))
save_table(balance,"balance_permutation")
stopifnot(nrow(age_effects)==27,nrow(age_tests)==9,nrow(fe_itt)==9,nrow(fe_iv)==5,sum(age_counts$n)==1176)
cat("Saved only the displayed slide analyses and their supporting counts to results/slide_regressions/.\n")
```

