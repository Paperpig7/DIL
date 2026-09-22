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
b <- read.csv(file.path(root, "data/raw/study_baseline.csv"), na.strings = c("", "NA"), check.names = FALSE)
f <- read.csv(file.path(root, "data/raw/study_followup.csv"), na.strings = c("", "NA"), check.names = FALSE)
dict <- read.csv(file.path(root, "data/raw/data_dictionary.csv"), check.names = FALSE)
stopifnot(!anyNA(b$applicant_id), !anyNA(f$applicant_id), !anyDuplicated(b$applicant_id), !anyDuplicated(f$applicant_id))
stopifnot(setequal(b$applicant_id, f$applicant_id))
d <- merge(b, f, by = "applicant_id", all.x = TRUE, sort = TRUE)
stopifnot(nrow(d) == nrow(b))
d$cohort <- factor(paste(d$municipality, d$application_year, sep = "_"), levels = c("A_2020", "A_2022", "B_2018"))
stopifnot(!anyNA(d$cohort))
weights <- prop.table(table(d$cohort))

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
d$repeats_conflict <- (!is.na(d$repeats_g6)&!is.na(d$total_repeats)&d$repeats_g6>d$total_repeats) |
  (!is.na(d$ever_repeated)&!is.na(d$total_repeats)&d$ever_repeated!=as.integer(d$total_repeats>0))
add_issue(d$repeats_conflict,"total_repeats","repetition_fields_disagree","inconsistent",
  "Retain reported primary total. Sensitivity excludes conflicting records.",
  paste0("g6=",d$repeats_g6,"; ever=",d$ever_repeated,"; total=",d$total_repeats))
d$private_school_conflict <- !is.na(d$in_private_now)&!is.na(d$in_school_now)&d$in_private_now==1&d$in_school_now==0
add_issue(d$private_school_conflict,"in_private_now","private_but_not_enrolled","inconsistent",
  "Retain source values and exclude conflicted records in outcome sensitivity.",paste0("private=",d$in_private_now,"; enrolled=",d$in_school_now))
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
d$work_hours_conflict <- !is.na(d$working)&!is.na(d$hours_worked)&d$working==0&d$hours_worked>0
add_issue(d$work_hours_conflict,"hours_worked","not_working_but_positive_hours","inconsistent",
  "Retain source fields. Show sensitivity excluding conflict for secondary work outcomes.",paste0("working=",d$working,"; hours=",d$hours_worked))
add_issue(!is.na(d$working)&!is.na(d$hours_worked)&d$working==1&d$hours_worked==0,"hours_worked","working_but_zero_weekly_hours","review",
  "Retain. Could reflect temporary absence or reference-period differences; do not assume zero means missing.")
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
contrast <- function(fit,L) {
  L <- L[names(fit$coef)]
  est <- sum(L*fit$coef); se <- sqrt(as.numeric(t(L)%*%fit$V%*%L))
  crit <- qt(.975,fit$df)
  data.frame(estimate=est,se=se,ci_low=est-crit*se,ci_high=est+crit*se,
    p_value=if(se>0) 2*pt(-abs(est/se),fit$df) else if(est==0) 1 else 0,n=fit$n,df=fit$df)
}
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
primary <- c("in_school_now","in_private_now","highest_grade","total_repeats")
labels <- c(in_school_now="Currently enrolled",in_private_now="Currently in private school",highest_grade="Highest grade completed",total_repeats="Total grade repetitions")
main <- do.call(rbind,lapply(primary,function(y) stratified(d,y)))
main$holm_p <- p.adjust(main$p_value,"holm")
main$label <- labels[main$outcome]
main$unit <- ifelse(main$outcome%in%c("in_school_now","in_private_now"),"proportion","grades")
write_table(main,"primary_effects")

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
for(v in c("age_at_application","ses_stratum")) {
  d[[paste0(v,"_imp")]] <- d[[v]]
  for(s in levels(d$cohort)) {
    ids <- which(d$cohort==s)
    mu <- mean(d[[v]][ids],na.rm=TRUE)
    if(!is.finite(mu)) mu <- mean(d[[v]],na.rm=TRUE)
    d[[paste0(v,"_imp")]][ids[is.na(d[[v]][ids])]] <- mu
  }
}
controls <- c("male","has_phone","age_at_application_imp","age_at_application_missing","ses_stratum_imp","ses_stratum_missing")
balfit <- robust_fit(as.formula(paste("selected ~ cohort +",paste(controls,collapse=" + "))),d)
tested <- intersect(controls,names(balfit$coef))
q <- length(tested); beta <- balfit$coef[tested]; vv <- balfit$V[tested,tested]
stat <- as.numeric(t(beta)%*%solve(vv,beta))/q
write_table(data.frame(test="Joint baseline balance, conditional on cohort",F_statistic=stat,numerator_df=q,denominator_df=balfit$df,p_value=pf(stat,q,balfit$df,lower.tail=FALSE)),"balance_joint_test")

# Outcomes are not imputed for primary estimates. Missingness itself is an outcome.
missing <- do.call(rbind,lapply(setdiff(names(f),"applicant_id"),function(v) {
  xx <- d; xx$item_missing <- as.integer(is.na(xx[[v]])); rr <- stratified(xx,"item_missing")
  rr$outcome <- v; rr$missing_control <- sum(is.na(xx[[v]])&xx$selected==0); rr$missing_selected <- sum(is.na(xx[[v]])&xx$selected==1)
  rr
}))
write_table(missing,"outcome_missingness")
missing_cohort <- do.call(rbind,lapply(primary,function(v) do.call(rbind,lapply(split(d,list(d$cohort,d$selected),drop=TRUE),function(x) data.frame(outcome=v,cohort=as.character(x$cohort[1]),selected=x$selected[1],n=nrow(x),missing=sum(is.na(x[[v]])))))))
write_table(missing_cohort,"primary_missingness_by_cohort")

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

# Secondary outcomes and mechanisms are explicitly exploratory.
secondary_names <- c("receiving_aid_now","started_g6_private","started_g7_private","finished_g6","finished_g7","finished_g8","ever_repeated","years_in_school","married_or_cohab","has_child","working","hours_worked")
secondary <- do.call(rbind,lapply(secondary_names,function(y) stratified(d,y)))
secondary$holm_p <- p.adjust(secondary$p_value,"holm")
write_table(secondary,"secondary_effects")
write_table(do.call(rbind,lapply(c("working","hours_worked"),function(y) stratified(d[!d$work_hours_conflict,],y))),"work_conflict_sensitivity")

# Diagnostic: post-assignment administrative/household variables are not controls.
admin <- do.call(rbind,lapply(c("survey_month","survey_form","household_visit","mother_educ","father_educ"),function(y) stratified(d,y)))
write_table(admin,"followup_descriptives")
write_table(as.data.frame(with(d,table(cohort,selected,male))),"cohort_assignment_sex_counts")

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

# REVISION 6: Estimate first stages, including entry and current attendance.
exposures <- c("in_private_now","started_g6_private","started_g7_private")
rev_fs <- do.call(rbind,lapply(levels(d$cohort),function(s) do.call(rbind,lapply(c(exposures,"receiving_aid_now"),function(y) {
  r <- cohort_itt(d[d$cohort==s,],y); r$cohort <- s; r$F_statistic <- (r$estimate/r$se)^2
  r$interpretation <- if(y=="receiving_aid_now") "Any current aid; not original program receipt" else "Lottery-offer effect on private-school indicator"
  r
}))))
write_table(rev_fs,"revised_first_stage")

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
