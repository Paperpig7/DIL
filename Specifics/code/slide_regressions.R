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

# CHUNK 4: Slide 9: reuse the three displayed current-private first stages.
first_stages <- itt[itt$outcome=="in_private_now",]
first_stages$F_statistic <- (first_stages$estimate/first_stages$se)^2
save_table(first_stages,"first_stages")

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
