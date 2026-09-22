# Independent finite-randomization balance check with a separate Monte Carlo seed.
options(stringsAsFactors=FALSE)
args<-commandArgs(trailingOnly=FALSE);script<-sub('^--file=','',args[grepl('^--file=',args)])
root<-if(length(script))dirname(dirname(normalizePath(script))) else normalizePath('.')
d<-read.csv(file.path(root,'data/raw/study_baseline.csv'));d$cohort<-paste(d$municipality,d$application_year,sep='_')
makeC<-function(x){a<-x$age_at_application;s<-x$ses_stratum;am<-as.integer(is.na(a));sm<-as.integer(is.na(s));a[is.na(a)]<-mean(a,na.rm=TRUE);s[is.na(s)]<-mean(s,na.rm=TRUE);C<-cbind(male=x$male,has_phone=x$has_phone,age=a,age_missing=am,ses=s,ses_missing=sm);C[,apply(C,2,sd)>0,drop=FALSE]}
set.seed(20260923);B<-19999;rows<-list()
for(co in c('A_2020','A_2022','B_2018')){
 x<-d[d$cohort==co,];C<-makeC(x);C<-sweep(C,2,colMeans(C));n<-nrow(C);n1<-sum(x$selected==1);n0<-n-n1;fac<-1/n1+1/n0
 V<-cov(C)*fac;Vinv<-solve(V);delta<-colMeans(C[x$selected==1,,drop=FALSE])-colMeans(C[x$selected==0,,drop=FALSE]);T<-drop(delta%*%Vinv%*%delta)
 simulated<-replicate(B,{j<-sample.int(n,n1);de<-colSums(C[j,,drop=FALSE])*fac;drop(de%*%Vinv%*%de)})
 p<-(1+sum(simulated>=T-1e-12))/(B+1)
 rows[[co]]<-data.frame(cohort=co,statistic=T,k=ncol(C),permutations=B,seed=20260923,p_randomization=p,MC_se=sqrt(p*(1-p)/(B+1)))
}
r<-do.call(rbind,rows);write.csv(r,file.path(root,'revision_iv_qc/independent_randomization_balance.csv'),row.names=FALSE);print(r,row.names=FALSE)
