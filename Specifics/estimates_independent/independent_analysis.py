"""Independent design-based replication, using only numpy/pandas and stdlib.
Raw files are read-only. Inference uses normal approximations with HC2 sandwich
covariance. Cohort-standardized estimates weight cohort differences by the full
baseline cohort shares, including for outcome item missingness. Observed-outcome
comparisons require an ignorable item-missingness assumption; bounds relax it.
"""
from pathlib import Path
from math import erfc, sqrt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
RAW = ROOT.parent / 'data' / 'raw'
b = pd.read_csv(RAW / 'study_baseline.csv')
f = pd.read_csv(RAW / 'study_followup.csv')
assert b.applicant_id.is_unique and f.applicant_id.is_unique
assert set(b.applicant_id)==set(f.applicant_id)
d = b.merge(f, on='applicant_id', validate='one_to_one')
d['cohort'] = d.municipality + d.application_year.astype(str)
cohorts = sorted(d.cohort.unique())
weights = d.cohort.value_counts(normalize=True).reindex(cohorts)
primary = ['in_school_now','in_private_now','highest_grade','total_repeats']
secondary = ['receiving_aid_now','started_g6_private','started_g7_private','finished_g6','finished_g7','finished_g8','repeats_g6','ever_repeated','years_in_school','married_or_cohab','has_child','working','hours_worked']

def ols(y,X,hc=2):
    y=np.asarray(y,float); X=np.asarray(X,float)
    inv=np.linalg.pinv(X.T@X)
    beta=inv@X.T@y
    resid=y-X@beta
    hat=np.sum((X@inv)*X, axis=1)
    u2=resid**2/(1-hat)**(hc-1)
    cov=inv@(X.T@(X*u2[:,None]))@inv
    return beta,cov

def norm_result(est,var):
    se=sqrt(max(0,float(var)))
    p=erfc(abs(est)/se/sqrt(2)) if se>0 else np.nan
    return dict(effect=float(est),se=se,low=float(est)-1.95996398454*se,high=float(est)+1.95996398454*se,p=p)

def saturated(data,y,sex=False,hc=2):
    z=data.dropna(subset=[y]).copy()
    labels=[(s,t,m) for s in cohorts for t in [0,1] for m in ([0,1] if sex else [None])]
    X=np.column_stack([((z.cohort==s)&(z.selected==t)&((z.male==m) if sex else True)).astype(float) for s,t,m in labels])
    beta,cov=ols(z[y],X,hc=hc)
    C=np.array([weights[s]*(1 if t else -1) for s,t,m in labels])
    if not sex:
        c0=np.array([weights[s]*(t==0) for s,t,m in labels]); c1=np.array([weights[s]*(t==1) for s,t,m in labels])
        r=norm_result(C@beta,C@cov@C);r.update(control_mean=c0@beta,treatment_mean=c1@beta,n=len(z),missing=len(data)-len(z))
        return r
    cs={m:np.array([weights[s]*(1 if t else -1)*(m==sx) for s,t,sx in labels]) for m in [0,1]}
    diff=cs[1]-cs[0]
    out=[]
    for label,c in [('female',cs[0]),('male',cs[1]),('male_minus_female',diff)]:
        r=norm_result(c@beta,c@cov@c);r.update(group=label,n=len(z));out.append(r)
    return out

def fe(data,y,adjust=False):
    z=data.dropna(subset=[y]).copy()
    X=[np.ones(len(z)), z.selected.values]
    X.extend((z.cohort==s).astype(float) for s in cohorts[1:])
    if adjust:
        X.extend([z.male.values,z.has_phone.values])
        for var in ['age_at_application','ses_stratum']:
            # Preserve sample: full-baseline cohort median imputation plus missing flag.
            med=d.groupby('cohort')[var].median()
            fill=z[var].fillna(z.cohort.map(med))
            X.extend([fill.values,z[var].isna().astype(float).values])
    beta,cov=ols(z[y],np.column_stack(X))
    r=norm_result(beta[1],cov[1,1]);r.update(n=len(z));return r

rows=[]
for y in primary+secondary:
    r=saturated(d,y);r.update(outcome=y,estimator='cohort_weighted_HC2');rows.append(r)
    r=saturated(d,y,hc=3);r.update(outcome=y,estimator='cohort_weighted_HC3');rows.append(r)
    r=fe(d,y);r.update(outcome=y,estimator='cohort_FE_HC2');rows.append(r)
    r=fe(d,y,adjust=True);r.update(outcome=y,estimator='covariate_adjusted_FE_HC2');rows.append(r)
results=pd.DataFrame(rows)
# Holm familywise correction of the 4 main unadjusted primary endpoint p-values.
ix=results.index[(results.outcome.isin(primary))&(results.estimator=='cohort_weighted_HC2')]
order=results.loc[ix].sort_values('p').index
last=0
for i,ind in enumerate(order):
    last=max(last,min(1,(len(order)-i)*results.loc[ind,'p']))
    results.loc[ind,'holm_primary_p']=last
results.to_csv(ROOT/'outcome_estimates.csv',index=False)

sexrows=[]
for y in primary+secondary:
    for r in saturated(d,y,sex=True):
        r.update(outcome=y);sexrows.append(r)
pd.DataFrame(sexrows).to_csv(ROOT/'sex_effects.csv',index=False)

cohortrows=[]
for y in primary+secondary:
    for s in cohorts:
        z=d.loc[d.cohort==s].dropna(subset=[y]); arm=z.groupby('selected')[y]
        r=norm_result(arm.mean()[1]-arm.mean()[0],arm.var()[1]/arm.count()[1]+arm.var()[0]/arm.count()[0])
        r.update(outcome=y,cohort=s,control_mean=arm.mean()[0],treatment_mean=arm.mean()[1],n=len(z));cohortrows.append(r)
pd.DataFrame(cohortrows).to_csv(ROOT/'cohort_effects.csv',index=False)

balrows=[]
for y in ['male','age_at_application','has_phone','ses_stratum']:
    r=saturated(d,y);r.update(variable=y);balrows.append(r)
    d[y+'_missing']=d[y].isna().astype(int)
    if d[y+'_missing'].sum():
        r=saturated(d,y+'_missing');r.update(variable=y+'_missing');balrows.append(r)
pd.DataFrame(balrows).to_csv(ROOT/'baseline_balance.csv',index=False)

missrows=[]
for y in primary+secondary:
    m=y+'_missing';d[m]=d[y].isna().astype(int)
    if d[m].sum():
        r=saturated(d,m);r.update(outcome=y);missrows.append(r)
pd.DataFrame(missrows).to_csv(ROOT/'item_missingness.csv',index=False)

# Logical value bounds: report point identification intervals, NOT confidence intervals.
boundrows=[]
for y,lb,ub in [('in_school_now',0,1),('in_private_now',0,1),('total_repeats',0,3)]:
    lower=upper=0
    for s in cohorts:
        z=d[d.cohort==s]
        a=z.loc[z.selected==1,y];c=z.loc[z.selected==0,y]
        lower+=weights[s]*(a.fillna(lb).mean()-c.fillna(ub).mean())
        upper+=weights[s]*(a.fillna(ub).mean()-c.fillna(lb).mean())
    boundrows.append(dict(outcome=y,identification_lower=lower,identification_upper=upper))
pd.DataFrame(boundrows).to_csv(ROOT/'missingness_bounds.csv',index=False)

# Outcome checks leave ambiguity flagged in primary; this sensitivity removes contradictory fields.
d['age_delta']=d.age_at_survey-d.age_at_application
conflict=((d.highest_grade>=6)&(d.finished_g6==0))|((d.highest_grade>=7)&(d.finished_g7==0))|((d.highest_grade>=8)&(d.finished_g8==0))
sensrows=[]
for label,mask in [('exclude_negative_age',~(d.age_delta<0)),('exclude_grade_conflicts',~conflict),('exclude_age_delta_outside_2_4',~((d.age_delta<2)|(d.age_delta>4)))]:
    for y in primary:
        r=saturated(d[mask],y);r.update(outcome=y,sensitivity=label);sensrows.append(r)
pd.DataFrame(sensrows).to_csv(ROOT/'sensitivity.csv',index=False)

print('PRIMARY:\n'+results.loc[(results.outcome.isin(primary))&(results.estimator=='cohort_weighted_HC2')].to_string(index=False))
print('\nSEX:\n'+pd.DataFrame(sexrows).query('outcome in @primary').to_string(index=False))
print('\nBALANCE:\n'+pd.DataFrame(balrows).to_string(index=False))
print('\nMISSING:\n'+pd.DataFrame(missrows).query('outcome in @primary').to_string(index=False))
print('\nBOUNDS:\n'+pd.DataFrame(boundrows).to_string(index=False))
