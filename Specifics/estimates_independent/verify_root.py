"""Cross-language numerical QC of the authoritative base R pipeline."""
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parent
raw=ROOT.parent/'data/raw'; tables=ROOT.parent/'results/tables'
d=pd.read_csv(raw/'study_baseline.csv').merge(pd.read_csv(raw/'study_followup.csv'),on='applicant_id',validate='one_to_one')
d['cohort']=d.municipality+'_'+d.application_year.astype(str)
cohorts=['A_2020','A_2022','B_2018']; w=d.cohort.value_counts(normalize=True).reindex(cohorts).values
primary=['in_school_now','in_private_now','highest_grade','total_repeats']

def ols(y,X,hc=2):
    y=np.asarray(y,float);X=np.asarray(X,float)
    # Independent QR/lstsq solution, unlike the R lm+sandwich implementation.
    beta=np.linalg.lstsq(X,y,rcond=None)[0]
    B=np.linalg.inv(X.T@X);e=y-X@beta;h=np.einsum('ij,jk,ik->i',X,B,X)
    V=B@(X.T@(X*(e**2/(1-h)**(hc-1))[:,None]))@B
    return beta,V

checks=[]
def check(label,got,expected):
    error=abs(float(got)-float(expected))
    checks.append(dict(check=label,python=got,R=expected,abs_difference=error,passed=error<1e-9))

def standard(data,y,hc=2):
    z=data.dropna(subset=[y]);X=np.column_stack([((z.cohort==s)&(z.selected==t)).astype(float) for s in cohorts for t in [0,1]])
    beta,V=ols(z[y],X,hc);C=np.array([ww*sign for ww in w for sign in [-1,1]])
    return C@beta,np.sqrt(C@V@C)

r=pd.read_csv(tables/'primary_effects.csv').set_index('outcome')
for y in primary:
    est,se=standard(d,y)
    check(y+' primary estimate',est,r.loc[y,'estimate']);check(y+' primary HC2 se',se,r.loc[y,'se'])

r=pd.read_csv(tables/'sex_effects.csv').set_index(['outcome','sex'])
for y in primary:
    z=d.dropna(subset=[y]);cells=[(s,t,sex) for s in cohorts for t in [0,1] for sex in [0,1]]
    X=np.column_stack([((z.cohort==s)&(z.selected==t)&(z.male==sex)).astype(float) for s,t,sex in cells])
    beta,V=ols(z[y],X)
    cs={sex:np.array([w[cohorts.index(s)]*(1 if t else -1)*(sx==sex) for s,t,sx in cells]) for sex in [0,1]}
    for label,C in [('Girls',cs[0]),('Boys',cs[1]),('Boys minus girls',cs[1]-cs[0])]:
        check(y+' '+label+' estimate',C@beta,r.loc[(y,label),'estimate'])
        check(y+' '+label+' se',np.sqrt(C@V@C),r.loc[(y,label),'se'])

# Replicate the revised adjusted model, with cohort-mean baseline imputation,
# all baseline covariates centered using all randomized applicants, and separate
# common covariate slopes by treatment. Missingness flags remain covariates.
controls=['male','has_phone']
for v in ['age_at_application','ses_stratum']:
    d[v+'_missing']=d[v].isna().astype(float)
    d[v+'_imp']=d[v].fillna(d.groupby('cohort')[v].transform('mean'))
    controls.extend([v+'_imp',v+'_missing'])
for v in controls:d[v+'_c']=d[v]-d.groupby('cohort')[v].transform('mean')
r=pd.read_csv(tables/'sensitivity_effects.csv').set_index(['outcome','specification'])
for y in primary:
    z=d.dropna(subset=[y]);cohortX=np.column_stack([(z.cohort==s).astype(float) for s in cohorts]);TX=cohortX*z.selected.values[:,None]
    covX=z[[v+'_c' for v in controls]].to_numpy()
    X=np.column_stack([cohortX,TX,covX,covX*z.selected.values[:,None]])
    beta,V=ols(z[y],X);C=np.r_[np.zeros(3),w,np.zeros(12)]
    rr=r.loc[(y,'Baseline-adjusted, assignment-interacted covariates')]
    check(y+' adjusted estimate',C@beta,rr.estimate);check(y+' adjusted se',np.sqrt(C@V@C),rr.se)

for y in primary:
    est,se=standard(d,y,hc=3);rr=r.loc[(y,'Primary point estimate, HC3 standard errors')]
    check(y+' HC3 estimate',est,rr.estimate);check(y+' HC3 se',se,rr.se)
    delta=d.age_at_survey-d.age_at_application
    mask=~(delta<0)
    est,se=standard(d[mask],y);rr=r.loc[(y,'Exclude 11 declining-age records')]
    check(y+' age exclusion estimate',est,rr.estimate);check(y+' age exclusion se',se,rr.se)
    conflict=np.zeros(len(d),bool)
    for g in [6,7,8]:conflict|=(d.highest_grade>=g)&(d['finished_g'+str(g)]==0)
    est,se=standard(d[~conflict],y);rr=r.loc[(y,'Exclude any primary schooling contradiction')]
    check(y+' grade exclusion estimate',est,rr.estimate);check(y+' grade exclusion se',se,rr.se)

r=pd.read_csv(tables/'missing_outcome_bounds.csv').set_index('outcome')
for y,ub in [('in_school_now',1),('in_private_now',1),('total_repeats',3)]:
    lo=hi=0
    for s,ww in zip(cohorts,w):
        z=d[d.cohort==s];a=z.loc[z.selected==1,y];c=z.loc[z.selected==0,y]
        lo+=ww*(a.fillna(0).mean()-c.fillna(ub).mean());hi+=ww*(a.fillna(ub).mean()-c.fillna(0).mean())
    check(y+' missing lower bound',lo,r.loc[y,'lower_bound']);check(y+' missing upper bound',hi,r.loc[y,'upper_bound'])

checks=pd.DataFrame(checks)
checks.to_csv(ROOT/'root_numerical_verification.csv',index=False)
print(checks.to_string(index=False))
assert checks.passed.all()
print(f'All {len(checks)} comparisons passed; max abs difference {checks.abs_difference.max():.3g}.')
