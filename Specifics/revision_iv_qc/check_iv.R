# Independent verification: base R only. Raw source values preserved.
options(stringsAsFactors=FALSE)
args<-commandArgs(trailingOnly=FALSE)
script<-sub('^--file=', '', args[grepl('^--file=',args)])
assessment_root<-if(length(script)) dirname(dirname(normalizePath(script))) else normalizePath('.')
b <- read.csv(file.path(assessment_root,'data/raw/study_baseline.csv'),na.strings=c('','NA'))
f <- read.csv(file.path(assessment_root,'data/raw/study_followup.csv'),na.strings=c('','NA'))
d <- merge(b,f,by='applicant_id',all.x=TRUE)
d$cohort <- paste(d$municipality,d$application_year,sep='_')
stopifnot(nrow(d)==nrow(b),!anyDuplicated(d$applicant_id))
out <- file.path(assessment_root,'revision_iv_qc')
# Joint reduced-form/first-stage covariance, preserving their covariance.
# HC1 is conventional structural-IV HC1; HC2 divides by the binary-Z
# regression leverage, giving a Welch-based ratio-delta sensitivity.
joint <- function(y,p,z,kind='HC1') {
  zz <- cbind(1,z); n<-length(y); k<-2
  fit<-lm.fit(zz,cbind(y,p)); bread<-solve(crossprod(zz))
  u<-fit$residuals
  leverage<-rowSums((zz%*%bread)*zz)
  scale<-if(kind=='HC1') rep(n/(n-k),n) else 1/(1-leverage)
  infl <- (zz%*%bread)[,2]*sqrt(scale)
  V<-crossprod(u*infl)
  c(rf=fit$coefficients[2,1],fs=fit$coefficients[2,2],v_rf=V[1,1],v_fs=V[2,2],cov=V[1,2])
}
# Solve a beta^2+b beta+c <=0, including nonstandard confidence sets.
quadratic_set <- function(a,b,c) {
  tol<-1e-12
  if(abs(a)<tol) {
    if(abs(b)<tol) return(if(c<=0)'all real numbers' else 'empty set')
    root <- -c/b
    return(if(b>0)sprintf('(-Inf, %.8f]',root) else sprintf('[%.8f, Inf)',root))
  }
  disc<-b*b-4*a*c
  if(disc<0)return(if(a<0)'all real numbers' else 'empty set')
  rr<-sort(c((-b-sqrt(disc))/(2*a),(-b+sqrt(disc))/(2*a)))
  if(a>0) sprintf('[%.8f, %.8f]',rr[1],rr[2]) else sprintf('(-Inf, %.8f] U [%.8f, Inf)',rr[1],rr[2])
}
# Direct robust 2SLS sandwich independent of ratio delta calculations.
structural_iv <- function(y,p,z) {
  X<-cbind(1,p); Z<-cbind(1,z); n<-length(y)
  Xhat<-Z%*%solve(crossprod(Z),crossprod(Z,X))
  b<-solve(crossprod(Xhat),crossprod(Xhat,y))
  u<-as.vector(y-X%*%b)
  bread<-solve(crossprod(Xhat))
  V<-bread%*%crossprod(Xhat*u)%*%bread*n/(n-2)
  c(beta=b[2],se=sqrt(V[2,2]))
}
Y<-c('years_in_school','married_or_cohab','has_child','working','hours_worked')
rows<-list(); itt<-list(); aid<-list()
for(co in c('A_2020','A_2022','B_2018')) {
  dat<-d[d$cohort==co,]
  for(y in c(Y,'in_school_now','in_private_now','highest_grade','total_repeats')) {
    sub<-dat[complete.cases(dat[,c(y,'selected')]),]
    n<-nrow(sub); n1<-sum(sub$selected==1); n0<-sum(sub$selected==0)
    y1<-sub[[y]][sub$selected==1]; y0<-sub[[y]][sub$selected==0]
    est<-mean(y1)-mean(y0); se<-sqrt(var(y1)/n1+var(y0)/n0)
    crit<-qt(.975,n-2); pval<-2*pt(-abs(est/se),n-2)
    itt[[length(itt)+1]]<-data.frame(cohort=co,outcome=y,n=n,n0=n0,n1=n1,mean_control=mean(y0),mean_offer=mean(y1),effect=est,se_HC2=se,lower=est-crit*se,upper=est+crit*se,p=pval)
  }
  for(y in Y) {
    sub<-dat[complete.cases(dat[,c(y,'in_private_now','selected')]),]
    for(hc in c('HC1','HC2')) {
      q<-joint(sub[[y]],sub$in_private_now,sub$selected,hc)
      beta<-q['rf']/q['fs']
      se<-sqrt((q['v_rf']-2*beta*q['cov']+beta^2*q['v_fs'])/q['fs']^2)
      if(hc=='HC1'){
        direct<-structural_iv(sub[[y]],sub$in_private_now,sub$selected)
        stopifnot(abs(beta-direct['beta'])<1e-10,abs(se-direct['se'])<1e-10)
      }
      crit<-if(hc=='HC2')qt(.975,nrow(sub)-2) else qnorm(.975); ar_a<-q['fs']^2-crit^2*q['v_fs'];ar_b<--2*q['rf']*q['fs']+2*crit^2*q['cov'];ar_c<-q['rf']^2-crit^2*q['v_rf']
      rows[[length(rows)+1]]<-data.frame(cohort=co,outcome=y,variance=hc,n=nrow(sub),n0=sum(sub$selected==0),n1=sum(sub$selected==1),ITT_same_sample=q['rf'],FS_same_sample=q['fs'],FS_se=sqrt(q['v_fs']),FS_F=q['fs']^2/q['v_fs'],IV_beta=beta,IV_se=se,IV_lower=beta-crit*se,IV_upper=beta+crit*se,IV_p=if(hc=='HC2')2*pt(-abs(beta/se),nrow(sub)-2) else 2*pnorm(-abs(beta/se)),AR_p_null0=if(hc=='HC2')2*pt(-abs(q['rf']/sqrt(q['v_rf'])),nrow(sub)-2) else pchisq(q['rf']^2/q['v_rf'],df=1,lower.tail=FALSE),AR_confset=quadratic_set(ar_a,ar_b,ar_c),var_rf=q['v_rf'],var_fs=q['v_fs'],cov_rf_fs=q['cov'])
    }
  }
  for(z in 0:1) {
    s<-dat[dat$selected==z,]
    aid[[length(aid)+1]]<-data.frame(cohort=co,selected=z,applicants=nrow(s),aid_observed=sum(!is.na(s$receiving_aid_now)),aid_mean=mean(s$receiving_aid_now,na.rm=TRUE),private_observed=sum(!is.na(s$in_private_now)),private_mean=mean(s$in_private_now,na.rm=TRUE))
  }
}
iv<-do.call(rbind,rows); itt<-do.call(rbind,itt); aid<-do.call(rbind,aid)
itt$p_Holm_five<-NA_real_
for(co in unique(itt$cohort)){
 ix<-which(itt$cohort==co & itt$outcome%in%Y); itt$p_Holm_five[ix]<-p.adjust(itt$p[ix],method='holm',n=5)
}
write.csv(iv,file.path(out,'independent_iv.csv'),row.names=FALSE)
write.csv(itt,file.path(out,'independent_itt.csv'),row.names=FALSE)
write.csv(aid,file.path(out,'aid_private_by_assignment.csv'),row.names=FALSE)


# Additional sensitivity: alternative schooling definitions and a prespecified
# set of baseline-only covariates. These change the IV estimand and assumptions.
# Parents' survey values, aid use and other post-lottery fields are not controls.
controls <- function(dat) {
  a<-dat$age_at_application; s<-dat$ses_stratum
  am<-as.integer(is.na(a));sm<-as.integer(is.na(s))
  a[is.na(a)]<-mean(a,na.rm=TRUE);s[is.na(s)]<-mean(s,na.rm=TRUE)
  cc<-cbind(male=dat$male,has_phone=dat$has_phone,age=a,ses=s,age_missing=am,ses_missing=sm)
  cc[,apply(cc,2,sd)>0,drop=FALSE]
}
additional<-list()
for(co in c('A_2020','A_2022','B_2018')){
  dat<-d[d$cohort==co,]
  C<-controls(dat)
  for(D in c('in_private_now','started_g6_private','started_g7_private'))for(y in Y)for(adjust in c(FALSE,TRUE)){
    ok<-complete.cases(dat[,c(y,D,'selected')])
    sub<-dat[ok,]; n<-nrow(sub)
    zz<-cbind(intercept=1,selected=sub$selected)
    if(adjust)zz<-cbind(zz,C[ok,,drop=FALSE])
    zz<-zz[,qr(zz)$pivot[seq_len(qr(zz)$rank)],drop=FALSE]
    fit<-lm.fit(zz,cbind(sub[[y]],sub[[D]]));k<-ncol(zz)
    B<-solve(crossprod(zz));h<-rowSums((zz%*%B)*zz)
    sc<-(zz%*%B)[,'selected']/sqrt(1-h)
    V<-crossprod(fit$residuals*sc)
    rf<-fit$coefficients['selected',1];fs<-fit$coefficients['selected',2]
    beta<-rf/fs;se<-sqrt((V[1,1]+beta^2*V[2,2]-2*beta*V[1,2])/fs^2)
    crit<-qt(.975,n-k)
    is_constant<-length(unique(sub[[y]]))<2
    ar<-quadratic_set(fs^2-crit^2*V[2,2],-2*rf*fs+2*crit^2*V[1,2],rf^2-crit^2*V[1,1])
    additional[[length(additional)+1]]<-data.frame(cohort=co,exposure=D,outcome=y,baseline_adjusted=adjust,n=n,k=k,n_control=sum(sub$selected==0),n_selected=sum(sub$selected==1),rf=rf,rf_se=sqrt(V[1,1]),fs=fs,fs_se=sqrt(V[2,2]),fs_F=fs^2/V[2,2],var_rf=V[1,1],var_fs=V[2,2],cov_rf_fs=V[1,2],ar_p=if(is_constant)NA else 2*pt(-abs(rf/sqrt(V[1,1])),n-k),beta=beta,se=if(is_constant)NA else se,lower=if(is_constant)NA else beta-crit*se,upper=if(is_constant)NA else beta+crit*se,p=if(is_constant)NA else 2*pt(-abs(beta/se),n-k),AR_set=if(is_constant)'Not reported: no outcome variation' else ar,constant_outcome=is_constant)
  }
}
write.csv(do.call(rbind,additional),file.path(out,'independent_iv_sensitivities.csv'),row.names=FALSE,na='')
# Avoid implying zero uncertainty when no events are observed in a whole cohort.
for(y in c('married_or_cohab','has_child')){
 ix<-iv$cohort=='A_2022'&iv$outcome==y
 iv[ix,c('IV_se','IV_lower','IV_upper','IV_p','AR_p_null0')]<-NA
 iv$AR_confset[ix]<-'Not reported: no observed events in either arm'
 ix<-itt$cohort=='A_2022'&itt$outcome==y
 itt[ix,c('se_HC2','lower','upper','p','p_Holm_five')]<-NA
}
write.csv(iv,file.path(out,'independent_iv.csv'),row.names=FALSE,na='')
write.csv(itt,file.path(out,'independent_itt.csv'),row.names=FALSE,na='')

print(itt[itt$cohort=='A_2020',],row.names=FALSE)
print(iv[iv$variance=='HC2',1:18],row.names=FALSE)
cat('Verified structural 2SLS point estimates/HC1 sandwich equal same-sample ratio delta in all 15 models.\n')
