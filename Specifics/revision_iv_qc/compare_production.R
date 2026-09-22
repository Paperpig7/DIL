# Independent numerical QC of the production revised CSVs. No package dependencies.
options(stringsAsFactors=FALSE)
args<-commandArgs(trailingOnly=FALSE)
script<-sub('^--file=', '', args[grepl('^--file=',args)])
root<-if(length(script)) dirname(dirname(normalizePath(script))) else normalizePath('.')
qc<-file.path(root,'revision_iv_qc'); tables<-file.path(root,'results/tables')
readq<-function(f)read.csv(file.path(qc,f),na.strings=c('','NA','NaN'))
readp<-function(f)read.csv(file.path(tables,f),na.strings=c('','NA','NaN'))
checks<-list()
record<-function(section,key,field,actual,expected,tol=1e-9){
 if(length(actual)!=1||length(expected)!=1)stop(paste('Non-scalar check',section,key,field,length(actual),length(expected)))
 equal<-if(is.na(expected))is.na(actual) else if(is.numeric(expected)&&is.numeric(actual))is.finite(actual)&&abs(actual-expected)<=tol else identical(as.character(actual),as.character(expected))
 checks[[length(checks)+1]]<<-data.frame(section=section,key=key,field=field,actual=as.character(actual),expected=as.character(expected),pass=isTRUE(equal))
}
pp<-rbind(readp('revised_policy_effects.csv'),readp('revised_schooling_effects.csv'))
ii<-readq('independent_itt.csv')
for(i in seq_len(nrow(pp))){
 r<-pp[i,]; e<-ii[ii$cohort==r$cohort & ii$outcome==r$outcome,];stopifnot(nrow(e)==1)
 key<-paste(r$cohort,r$outcome,sep='/')
 mp<-c(n='n',n_control='n0',n_selected='n1',control_mean='mean_control',selected_mean='mean_offer',estimate='effect',se='se_HC2',ci_low='lower',ci_high='upper',p_value='p')
 for(f in names(mp))record('ITT',key,f,r[[f]],e[[mp[f]]])
 if(r$outcome%in%c('years_in_school','married_or_cohab','has_child','working','hours_worked'))record('ITT',key,'Holm five',r$holm_p,e$p_Holm_five)
}
# Verify both multiplicity families and all-nine correction explicitly (including missing p-values).
for(co in unique(pp$cohort)){
 for(fam in unique(pp$family)){
  ix<-pp$cohort==co&pp$family==fam; expect<-p.adjust(pp$p_value[ix],'holm',n=sum(ix))
  for(j in seq_along(expect))record('Holm',paste(co,fam,j,sep='/'),'family p',pp$holm_p[ix][j],expect[j])
 }
 ix<-pp$cohort==co;expect<-p.adjust(pp$p_value[ix],'holm',n=9)
 for(j in seq_along(expect))record('Holm',paste(co,j,sep='/'),'all-nine p',pp$holm_all_nine_p[ix][j],expect[j])
}
v<-rbind(readp('revised_iv_effects.csv'),readp('revised_iv_entry_sensitivity.csv'))
eiv<-readq('independent_iv_sensitivities.csv');stopifnot(nrow(v)==90,nrow(eiv)==90)
for(i in seq_len(nrow(v))){
 r<-v[i,];e<-eiv[eiv$cohort==r$cohort&eiv$exposure==r$exposure&eiv$outcome==r$outcome&eiv$baseline_adjusted==r$baseline_adjusted,];stopifnot(nrow(e)==1)
 key<-paste(r$cohort,r$exposure,r$outcome,r$baseline_adjusted,sep='/')
 mp<-c(n='n',n_control='n_control',n_selected='n_selected',reduced_form='rf',reduced_form_se='rf_se',first_stage='fs',first_stage_se='fs_se',first_stage_F='fs_F',estimate='beta',se='se',ci_low='lower',ci_high='upper',p_value='p',ar_p_zero='ar_p',var_rf='var_rf',var_fs='var_fs',cov_rf_fs='cov_rf_fs')
 for(f in names(mp))record('IV',key,f,r[[f]],e[[mp[f]]])
 record('IV',key,'df',r$df,e$n-e$k)
 if(e$constant_outcome){record('IV inference',key,'zero-event suppression',r$ar_type,'not reported');record('IV inference',key,'AR lower',r$ar_low,NA_real_);record('IV inference',key,'AR upper',r$ar_high,NA_real_)}else{
  exptype<-if(grepl('all real',e$AR_set))'all real' else if(grepl(' U ',e$AR_set))'disjoint' else if(grepl('empty',e$AR_set))'empty' else 'bounded'
  record('AR set',key,'type',r$ar_type,exptype)
  if(exptype%in%c('bounded','disjoint')){
   nums<-as.numeric(regmatches(e$AR_set,gregexpr('-?[0-9]+\\.?[0-9]*',e$AR_set))[[1]])
   record('AR set',key,'lower',r$ar_low,nums[1],tol=1e-7);record('AR set',key,'upper',r$ar_high,nums[2],tol=1e-7)
  }
 }
}
for(co in unique(v$cohort))for(ex in unique(v$exposure))for(adj in c(FALSE,TRUE)){
 ix<-v$cohort==co&v$exposure==ex&v$baseline_adjusted==adj
 expect<-p.adjust(v$ar_p_zero[ix],'holm',n=5)
 for(j in seq_along(expect))record('IV Holm',paste(co,ex,adj,j,sep='/'),'AR Holm five',v$holm_ar_p[ix][j],expect[j])
}
# Independently reconstruct each school transition count and record identifiers.
b<-read.csv(file.path(root,'data/raw/study_baseline.csv'));f<-read.csv(file.path(root,'data/raw/study_followup.csv'));d<-merge(b,f,by='applicant_id');d$cohort<-paste(d$municipality,d$application_year,sep='_')
tr<-readp('revised_transition_summary.csv')
for(i in seq_len(nrow(tr))){
 r<-tr[i,];s<-d[d$cohort==r$cohort&d$selected==r$selected,]
 prior<-!is.na(s[[r$from]])&s[[r$from]]==1; known<-prior&!is.na(s[[r$to]]);exit<-known&s[[r$to]]==0
 expected<-list(prior_private=sum(prior),paired_observed=sum(known),later_unknown=sum(prior&is.na(s[[r$to]])),exits=sum(exit),exit_fraction=sum(exit)/sum(known),exits_currently_enrolled=sum(exit&!is.na(s$in_school_now)&s$in_school_now==1),exits_not_currently_enrolled=sum(exit&!is.na(s$in_school_now)&s$in_school_now==0),exits_enrollment_unknown=sum(exit&is.na(s$in_school_now)))
 key<-paste(r$cohort,r$selected,r$from,r$to,sep='/')
 for(nm in names(expected))record('Transition',key,nm,r[[nm]],expected[[nm]])
}
exits<-read.csv(file.path(root,'data/derived/private_school_exit_records.csv'))
ids<-d$applicant_id[((!is.na(d$started_g6_private)&d$started_g6_private==1)|(!is.na(d$started_g7_private)&d$started_g7_private==1))&!is.na(d$in_private_now)&d$in_private_now==0]
record('Transition','record level','exact source IDs',paste(sort(exits$applicant_id),collapse=','),paste(sort(ids),collapse=','))
# Bound calculations use randomized-cohort denominators, including missing outcomes.
bo<-readp('revised_binary_missing_bounds.csv');a20<-d[d$cohort=='A_2020',]
for(i in seq_len(nrow(bo))){r<-bo[i,];y<-r$outcome;y1<-a20[[y]][a20$selected==1];y0<-a20[[y]][a20$selected==0];e<-c(lower=sum(y1,na.rm=TRUE)/length(y1)-(sum(y0,na.rm=TRUE)+sum(is.na(y0)))/length(y0),upper=(sum(y1,na.rm=TRUE)+sum(is.na(y1)))/length(y1)-sum(y0,na.rm=TRUE)/length(y0));for(nm in names(e))record('Missing bounds',y,nm,r[[nm]],e[[nm]])}
# Ancillary revised tables: first stages, missingness, baseline balance,
# primary sensitivity models, and sex interactions are checked from raw data.
arm_expected<-function(x,y,hc='HC2',suppress=TRUE){
 z<-x$selected; keep<-!is.na(x[[y]])&!is.na(z);z<-z[keep];Y<-x[[y]][keep]
 y0<-Y[z==0];y1<-Y[z==1];n0<-length(y0);n1<-length(y1);n<-n0+n1;df<-n-2
 estimate<-mean(y1)-mean(y0);se<-sqrt(var(y0)/(if(hc=='HC2')n0 else n0-1)+var(y1)/(if(hc=='HC2')n1 else n1-1));crit<-qt(.975,df)
 ans<-c(estimate=estimate,se=se,ci_low=estimate-crit*se,ci_high=estimate+crit*se,p_value=2*pt(-abs(estimate/se),df),n=n,df=df,control_mean=mean(y0),selected_mean=mean(y1),n_control=n0,n_selected=n1)
 if(suppress&&length(unique(Y))<2)ans[c('se','ci_low','ci_high','p_value')]<-NA
 if(!suppress&&se==0&&estimate==0)ans['p_value']<-1
 ans
}
for(vv in c('age_at_application','ses_stratum','neighborhood'))d[[paste0(vv,'_missing')]]<-as.integer(is.na(d[[vv]]))
for(nm in c('revised_first_stage.csv','revised_missingness.csv','revised_baseline_balance.csv')){
 tt<-readp(nm)
 for(i in seq_len(nrow(tt))){
  r<-tt[i,];x<-d[d$cohort==r$cohort,];y<-r$outcome
  if(nm=='revised_missingness.csv'){x$missing<-as.integer(is.na(x[[y]]));y<-'missing'}
  e<-arm_expected(x,y,suppress=nm!='revised_missingness.csv');key<-paste(r$cohort,r$outcome,sep='/')
  for(ff in names(e))record(nm,key,ff,r[[ff]],e[[ff]])
  if(nm=='revised_first_stage.csv')record(nm,key,'F_statistic',r$F_statistic,(e['estimate']/e['se'])^2)
  if(nm=='revised_baseline_balance.csv'){
   sdpool<-sqrt((var(x[[y]][x$selected==0],na.rm=TRUE)+var(x[[y]][x$selected==1],na.rm=TRUE))/2)
   expect<-if(is.finite(sdpool)&&sdpool>0)e['estimate']/sdpool else NA_real_
   record(nm,key,'standardized_difference',r$standardized_difference,expect)
  }
  if(nm=='revised_missingness.csv'){
   expect<-c(missing_control=sum(x$selected==0&x$missing==1),missing_selected=sum(x$selected==1&x$missing==1),observed_control=sum(x$selected==0&x$missing==0),observed_selected=sum(x$selected==1&x$missing==0))
   for(ff in names(expect))record(nm,key,ff,r[[ff]],expect[[ff]])
  }
 }
}
# A separate direct matrix sandwich avoids relying on production estimators.
robust_qc<-function(X,Y){
 ok<-complete.cases(X,Y);X<-X[ok,,drop=FALSE];Y<-Y[ok];X<-X[,qr(X)$pivot[seq_len(qr(X)$rank)],drop=FALSE]
 B<-solve(crossprod(X));bb<-solve(crossprod(X),crossprod(X,Y));uu<-drop(Y-X%*%bb);h<-rowSums((X%*%B)*X)
 V<-B%*%crossprod(X*(uu/sqrt(1-h)))%*%B
 list(b=bb,V=V,n=nrow(X),df=nrow(X)-ncol(X))
}
makeC<-function(x){a<-x$age_at_application;s<-x$ses_stratum;am<-as.integer(is.na(a));sm<-as.integer(is.na(s));a[is.na(a)]<-mean(a,na.rm=TRUE);s[is.na(s)]<-mean(s,na.rm=TRUE);C<-cbind(male=x$male,has_phone=x$has_phone,age=a,age_missing=am,ses=s,ses_missing=sm);C[,apply(C,2,sd)>0,drop=FALSE]}
jj<-readp('revised_balance_joint_test.csv')
for(i in seq_len(nrow(jj))){r<-jj[i,];x<-d[d$cohort==r$cohort,];C<-makeC(x);fit<-robust_qc(cbind(intercept=1,C),x$selected);q<-ncol(C);bb<-fit$b[-1,];Fv<-drop(t(bb)%*%solve(fit$V[-1,-1,drop=FALSE],bb))/q;e<-c(F_statistic=Fv,numerator_df=q,denominator_df=fit$df,p_value=pf(Fv,q,fit$df,lower.tail=FALSE),n=fit$n);for(ff in names(e))record('Baseline joint',r$cohort,ff,r[[ff]],e[[ff]])}
a20<-d[d$cohort=='A_2020',]
sex<-readp('revised_sex_effects.csv')
for(i in seq_len(nrow(sex))){r<-sex[i,];y<-r$outcome;x<-a20[!is.na(a20[[y]]),];girls<-arm_expected(x[x$male==0,],y,suppress=FALSE);boys<-arm_expected(x[x$male==1,],y,suppress=FALSE)
 estimate<-switch(r$sex,'Girls'=girls['estimate'],'Boys'=boys['estimate'],'Boys minus girls'=boys['estimate']-girls['estimate']);se<-switch(r$sex,'Girls'=girls['se'],'Boys'=boys['se'],'Boys minus girls'=sqrt(girls['se']^2+boys['se']^2));n<-nrow(x);df<-n-4;crit<-qt(.975,df)
 expect<-c(estimate=unname(estimate),se=unname(se),ci_low=unname(estimate-crit*se),ci_high=unname(estimate+crit*se),p_value=unname(2*pt(-abs(estimate/se),df)),n=n,df=df,subgroup_n=if(r$sex=='Girls')sum(x$male==0) else if(r$sex=='Boys')sum(x$male==1) else n)
 for(ff in names(expect))record('Sex interactions',paste(y,r$sex,sep='/'),ff,r[[ff]],expect[[ff]])
}
for(fam in list(c('years_in_school','married_or_cohab','has_child','working','hours_worked'),c('in_school_now','in_private_now','highest_grade','total_repeats'))){ix<-sex$sex=='Boys minus girls'&sex$outcome%in%fam;exp<-p.adjust(sex$p_value[ix],'holm',n=length(fam));for(j in seq_along(exp))record('Sex interactions',sex$outcome[ix][j],'Holm interaction',sex$holm_interaction_p[ix][j],exp[j])}
# Reconstruct contradiction flags only from original reports.
a20$age_decreased<-!is.na(a20$age_at_application)&!is.na(a20$age_at_survey)&a20$age_at_survey<a20$age_at_application
a20$logic_flag<-FALSE
for(g in 6:8){vv<-paste0('finished_g',g);a20$logic_flag<-a20$logic_flag|(!is.na(a20[[vv]])&!is.na(a20$highest_grade)&a20[[vv]]!=as.integer(a20$highest_grade>=g))}
a20$logic_flag<-a20$logic_flag|(!is.na(a20$repeats_g6)&!is.na(a20$total_repeats)&a20$repeats_g6>a20$total_repeats)|(!is.na(a20$ever_repeated)&!is.na(a20$total_repeats)&a20$ever_repeated!=as.integer(a20$total_repeats>0))|(!is.na(a20$in_private_now)&!is.na(a20$in_school_now)&a20$in_private_now==1&a20$in_school_now==0)
a20$work_conflict<-!is.na(a20$working)&!is.na(a20$hours_worked)&a20$working==0&a20$hours_worked>0
ss<-readp('revised_policy_sensitivity.csv')
for(i in seq_len(nrow(ss))){r<-ss[i,];x<-a20
 if(r$specification=='Exclude declining-age records')x<-x[!x$age_decreased,]
 if(r$specification=='Exclude schooling contradictions')x<-x[!x$logic_flag,]
 if(r$specification=='Exclude work-hours contradiction')x<-x[!x$work_conflict,]
 if(r$specification=='Baseline adjustment with assignment interactions'){
  C<-makeC(x);C<-sweep(C,2,colMeans(C));XC<-C*x$selected;colnames(XC)<-paste0('inter_',colnames(C));fit<-robust_qc(cbind(intercept=1,selected=x$selected,C,XC),x[[r$outcome]])
  estimate<-unname(fit$b['selected',]);se<-unname(sqrt(fit$V['selected','selected']));crit<-qt(.975,fit$df);n1<-sum(!is.na(x[[r$outcome]])&x$selected==1);n0<-sum(!is.na(x[[r$outcome]])&x$selected==0)
  e<-c(estimate=estimate,se=se,ci_low=estimate-crit*se,ci_high=estimate+crit*se,p_value=2*pt(-abs(estimate/se),fit$df),n=fit$n,df=fit$df,control_mean=NA,selected_mean=NA,n_control=n0,n_selected=n1)
 }else e<-arm_expected(x,r$outcome,hc=if(r$specification=='HC3 standard errors')'HC3' else 'HC2')
 for(ff in names(e))record('Policy sensitivity',paste(r$outcome,r$specification,sep='/'),ff,r[[ff]],e[[ff]])
}

# Reproduce the finite randomization simulation from independently constructed
# baseline matrices with the same documented RNG seed and fixed group sizes.
set.seed(20260922);Bp<-9999
rp<-readp('revised_balance_permutation.csv')
for(co in c('A_2020','A_2022','B_2018')){
 x<-d[d$cohort==co,];C<-makeC(x);C<-sweep(C,2,colMeans(C));n<-nrow(C);n1<-sum(x$selected==1);n0<-n-n1;fac<-1/n1+1/n0
 IV<-solve(cov(C)*fac);delta<-colMeans(C[x$selected==1,,drop=FALSE])-colMeans(C[x$selected==0,,drop=FALSE]);T<-drop(delta%*%IV%*%delta)
 sim<-replicate(Bp,{j<-sample.int(n,n1,replace=FALSE);dd<-colSums(C[j,,drop=FALSE])*fac;drop(dd%*%IV%*%dd)})
 p<-(1+sum(sim>=T-1e-12))/(Bp+1);r<-rp[rp$cohort==co,]
 expect<-c(n=n,n_selected=n1,n_control=n0,covariates=ncol(C),mahalanobis_statistic=T,permutations=Bp,p_value=p,monte_carlo_se=sqrt(p*(1-p)/(Bp+1)))
 for(ff in names(expect))record('Randomization balance',co,ff,r[[ff]],expect[[ff]])
}

res<-do.call(rbind,checks);write.csv(res,file.path(qc,'production_numerical_qc.csv'),row.names=FALSE)
summary<-aggregate(pass~section,res,function(x)c(checks=length(x),passed=sum(x),failed=sum(!x)))
print(summary,row.names=FALSE)
if(any(!res$pass))print(res[!res$pass,],row.names=FALSE)
writeLines(c(sprintf('Production numerical QC: %d checks; %d passed; %d failed.',nrow(res),sum(res$pass),sum(!res$pass)),'Compared all 27 cohort/outcome policy and schooling ITTs and all 90 cohort/exposure/outcome/adjustment IV rows.','Verified exact samples, HC2 covariance, estimates, standard errors, t confidence intervals, robust AR sets and explicit full-family Holm correction.','Verified no-event inference suppression, school-transition count summaries and source record IDs, and logical missing-outcome bounds.','Also checked every revised first-stage, missingness, baseline balance, baseline joint Wald diagnostic, sex-interaction and policy-sensitivity table.','Independently reconstructed conditional-randomization balance matrices and exactly reproduced statistic, p and MCSE using documented seed20260922/B9999/sample.int.'),file.path(qc,'production_qc_verdict.txt'))
stopifnot(all(res$pass))
