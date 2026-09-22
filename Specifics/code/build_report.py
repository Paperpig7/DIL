"""Build revised report from authoritative R tables. Requires Python + ReportLab.
Run after code/run_analysis.R; all paths are relative and raw files are unchanged.
"""
from pathlib import Path
import csv, re, html, math
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'report'; OUT.mkdir(exist_ok=True)
def read_path(p):
    with p.open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
def read(n):return read_path(ROOT/'results/tables'/f'{n}.csv')
P=['years_in_school','married_or_cohab','has_child','working','hours_worked']
S=['in_school_now','in_private_now','highest_grade','total_repeats']
B={'married_or_cohab','has_child','working','in_school_now','in_private_now','started_g6_private','started_g7_private','receiving_aid_now'}
L={'years_in_school':'School years since allocation','married_or_cohab':'Married / cohabiting','has_child':'Has a child','working':'Doing paid work','hours_worked':'Weekly work hours','in_school_now':'Currently enrolled','in_private_now':'Currently private','highest_grade':'Highest grade completed','total_repeats':'Grade repetitions','started_g6_private':'Started G6 privately','started_g7_private':'Started G7 privately'}
policy=read('revised_policy_effects'); school=read('revised_schooling_effects'); first=read('revised_first_stage')
iv=read('revised_iv_effects'); entry=read('revised_iv_entry_sensitivity'); sens=read('revised_policy_sensitivity')
miss=read('revised_missingness'); balance=read('revised_baseline_balance'); perm=read('revised_balance_permutation')
sex=read('revised_sex_effects'); cohort=read('cohort_summary'); bounds=read('revised_binary_missing_bounds')
neg=read_path(ROOT/'data/derived/age_decreased_records.csv'); grade=read_path(ROOT/'data/derived/schooling_conflict_records.csv')
def norm(s):return s.replace('_','')
def one(rows,y=None,c='A2020',**kw):
    rr=[r for r in rows if (y is None or r.get('outcome')==y) and norm(r.get('cohort','A2020'))==norm(c) and all(r.get(k)==v for k,v in kw.items())]
    if len(rr)!=1:raise ValueError(f'Expected one row: {y}/{c}/{kw}, found {len(rr)}')
    return rr[0]
def ok(x):
    try:return math.isfinite(float(x))
    except (TypeError,ValueError):return False
def v(x,m=1,d=2):return f'{float(x)*m:.{d}f}' if ok(x) else 'NR'
def p(x):return ('<0.001' if float(x)<.001 else f'{float(x):.3f}') if ok(x) else 'NR'
def m(y):return 100 if y in B else 1
def d(y):return 2 if y in B or y=='hours_worked' else 3
def lab(y):return L[y]+(' (pp)' if y in B else '')
def ci(r,y):return f"[{v(r['ci_low'],m(y),d(y))}, {v(r['ci_high'],m(y),d(y))}]" if ok(r['ci_low']) and ok(r['ci_high']) else 'NR'
def ar(r,y):
    if r['ar_type']=='bounded':return f"[{v(r['ar_low'],m(y),d(y))}, {v(r['ar_high'],m(y),d(y))}]"
    if not ok(r['ar_p_zero']):return 'NR: no events'
    return re.sub(r'(?<![A-Za-z])[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',lambda q:v(q.group(),m(y),d(y)),r['ar_set'])
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Body',fontName='Helvetica',fontSize=9.7,leading=13.4,spaceAfter=8,textColor=colors.HexColor('#263746')))
styles.add(ParagraphStyle(name='Small',fontName='Helvetica',fontSize=8.3,leading=11.1,spaceAfter=6,textColor=colors.HexColor('#526575')))
styles.add(ParagraphStyle(name='Cell',fontName='Helvetica',fontSize=8.1,leading=10.7))
styles.add(ParagraphStyle(name='Head',fontName='Helvetica-Bold',fontSize=8,leading=10.2,textColor=colors.white))
styles['Title'].fontName='Helvetica-Bold';styles['Title'].fontSize=25;styles['Title'].leading=29;styles['Title'].alignment=TA_LEFT
styles['Title'].textColor=colors.HexColor('#143448')
styles['Heading1'].fontSize=18;styles['Heading1'].leading=22;styles['Heading1'].spaceAfter=12;styles['Heading1'].textColor=colors.HexColor('#143448')
styles['Heading2'].fontSize=11.6;styles['Heading2'].leading=15;styles['Heading2'].spaceBefore=8;styles['Heading2'].spaceAfter=6;styles['Heading2'].textColor=colors.HexColor('#087E8B')
story=[];md=[]
def plain(t):
    t=re.sub(r'<link href="([^"]+)"[^>]*>(.*?)</link>',r'[\2](\1)',t)
    return html.unescape(re.sub('<[^>]+>','',t.replace('<br/>',' ').replace('<b>','**').replace('</b>','**')))
def h(t,sub=False):story.append(Paragraph(t,styles['Heading2' if sub else 'Heading1']));md.append(('### ' if sub else '## ')+plain(t)+'\n')
def para(t,small=False):story.append(Paragraph(t,styles['Small' if small else 'Body']));md.append(plain(t)+'\n')
def page(t):story.append(PageBreak());md.append('\n---\n');h(t)
def table(head,rows,widths):
    assert sum(widths)==528
    data=[[Paragraph(html.escape(str(x)),styles['Head']) for x in head]]+[[Paragraph(html.escape(str(x)),styles['Cell']) for x in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#143448')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#D5DFE5')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F3F6F8')])]))
    story.extend([t,Spacer(1,8)]);md.append('| '+' | '.join(head)+' |\n| '+' | '.join(['---']*len(head))+' |')
    md.extend('| '+' | '.join(str(x).replace('|','\\|') for x in row)+' |' for row in rows);md.append('')
def effects(rows,ys,c='A2020',mean=False):
    out=[]
    for y in ys:
        r=one(rows,y,c); a=[lab(y)]
        if mean:a.append(v(r['control_mean'],m(y),d(y)))
        out.append(a+[v(r['estimate'],m(y),d(y)),ci(r,y),p(r['p_value']),p(r['holm_p']),r['n']])
    return out

# Page 1: the policy question and principal result.
story.append(Paragraph('Government subsidies,<br/>schooling and life outcomes',styles['Title']));md.append('# Government subsidies, schooling and life outcomes\n')
para('DIL applied assessment | Revised draft for applicant review | September 22, 2026',True)
para('<b>Main population: municipality A, 2020 lottery applicants.</b> The policy question is whether offering the subsidy changes schooling, family formation and work. A2022 and B2018 are separate checks and do not enter the main estimate.')
para('<b>The offer increases private-school attendance, but the five broader policy outcomes remain uncertain.</b> A2020 point estimates indicate slightly more schooling and less family formation and work. None of the five tests survives Holm adjustment. Weekly hours is nominally significant and should be described as suggestive rather than conclusive.')
h('Five policy outcomes: A2020 offer effects',True)
table(['Outcome','Control mean','Offer effect','95% CI','Raw p','Holm p','N'],effects(policy,P,mean=True),[142,63,61,117,47,49,49])
para('Binary control means are percentages; effects and intervals are percentage points (pp). School years and weekly hours use original units. Confidence intervals are individual 95% HC2/t intervals. Holm p-values cover five policy outcomes. NR means inference is not reported.',True)
para('The offer raises current private attendance by <b>15.91 pp</b> in A2020. This is a policy response and a first stage for an exploratory IV analysis. It does not establish that private schooling alone caused changes in the five outcomes.')
h('Three distinct questions',True)
para('The lottery-offer effect is the principal causal policy estimand. Recipient ATT requires verified receipt histories that are unavailable. Private-school IV results require additional assumptions, including exclusion and no defiers. The report preserves unusual values, identifies exact conflicting records and shows targeted sensitivity checks.')

# Page 2: population and randomization diagnostics.
page('1. Study design and population')
para('The subsidy helps low-income students pay for private secondary school from grade 6. Renewal depends on academic progress and advancement. Oversubscribed municipalities allocate offers by lottery. Each applicant has one baseline and one follow-up record, with recalled schooling histories; the file is not a multiwave panel of contemporaneous school measurements.')
table(['Cohort','Applicants','Selected','Not selected','Offer rate','Role'],[[r['cohort'].replace('_',' '),r['n'],r['selected'],r['control'],v(r['selected_share'],100,1)+'%','Primary' if norm(r['cohort'])=='A2020' else 'Separate check'] for r in cohort],[86,79,79,87,80,117])
para('The main target is the 1,176 supplied A2020 applicants, not all municipal residents. The A2020 focus follows the applicant\'s clarification; no underlying emails were supplied or independently verified. All 1,618 IDs are unique and match one-to-one across files. This does not establish coverage of the original eligible lottery roster.')
h('A2020 baseline balance',True)
bl={'male':'Male (%)','age_at_application':'Baseline age','has_phone':'Phone recorded (%)','ses_stratum':'SES stratum','age_at_application_missing':'Baseline age missing (%)','ses_stratum_missing':'SES missing (%)','neighborhood_missing':'Neighborhood missing (%)'}
rows=[]
for r in balance:
    if norm(r['cohort'])!='A2020':continue
    y=r['outcome']; mult=1 if y in ['age_at_application','ses_stratum'] else 100
    rows.append([bl.get(y,y),v(r['control_mean'],mult),v(r['selected_mean'],mult),v(r['standardized_difference'],1,3),p(r['p_value'])])
table(['Characteristic','Control','Selected','Std. difference','p'],rows,[194,77,77,99,81])
para('The primary joint check randomly relabels assignment 9,999 times within each cohort, holding arm counts and the full-baseline covariance fixed, and compares a Mahalanobis balance statistic (seed 20260922). A2020 p = <b>0.6038</b> (Monte Carlo SE 0.0049); A2022 p = 0.1162; B2018 p = 0.0152. This calibration assumes the stated applicant lottery and does not prove its implementation.')
para('B2018 has notable age and phone imbalances, warranting caution. A sparse A2022 missing-age indicator makes a secondary HC2 joint-Wald diagnostic unstable; all five missing baseline ages are controls. Its extreme p-value is not used as evidence that the lottery failed. Individual balance p-values above are descriptive diagnostics.',True)

# Page 3: estimand, inference and missingness.
page('2. Estimation and missing responses')
para('<b>Unit:</b> applicant. <b>Assignment:</b> Z = selected in the lottery. For each cohort and outcome separately, fit <b>Y = alpha + tau Z + error</b>. Tau is the selected-minus-nonselected mean difference, estimating the intention-to-treat effect of the offer under valid assignment and response assumptions.')
para('The A2020 primary model has an intercept and assignment only. Binary outcomes use linear mean differences for interpretation in percentage points. Outcomes are not restricted to applicants who are privately schooled, enrolled, working, receiving aid or complete on other outcomes. Weekly hours includes reported zero hours.')
para('<b>Inference:</b> applicant-level HC2 standard errors with t-reference intervals and residual degrees of freedom. The unadjusted two-group variance equals s1 squared/n1 + s0 squared/n0. The municipality-year cohorts are strata, not three treatment clusters. Household/school links would be needed to assess dependence and spillovers; current school choice must not define post-treatment clusters.')
h('A2020 item missingness',True)
table(['Outcome','Missing control','Missing selected','Applicants','Difference p'],[[L[y],one(miss,y)['missing_control'],one(miss,y)['missing_selected'],one(miss,y)['n'],p(one(miss,y)['p_value'])] for y in P+S],[197,89,89,70,83])
para('Primary models omit only missing values of their own outcome. Full-applicant interpretation additionally requires observed responses to represent their assignment arm; similar response rates cannot establish this. IV models require both outcome and private-school status, so their sample sizes differ from the policy ITTs.',True)
para('The policy five form one Holm family; the retained schooling four form another. These families were chosen during this revision, not preregistered. The combined nine-outcome correction is a broader sensitivity. Confidence intervals are individual, not simultaneous. In A2022 zero-event family outcomes, descriptive means remain reported but degenerate normal/t intervals and p-values are suppressed.')

# Page 4: substantive policy interpretation and adjustment.
page('3. Interpreting the five policy outcomes')
para('<b>School years since allocation:</b> the estimate is small and its interval includes zero. The outcome is reported years completed since allocation, not lifetime attainment. The accounting convention and follow-up dates remain uncertain; retain the source values and their timing flags.')
para('<b>Marriage/cohabitation and parenthood:</b> negative estimates are imprecise, with uncommon events. The data do not establish prevention or delay of family formation. Current status does not date when an event occurred.')
para('<b>Paid work and hours:</b> both estimates point downward. Mean hours covers everyone with observed hours, including zeros, and combines whether and how much applicants work. Conditioning on working would select on a possible treatment response. Less work may free time for school, but without earnings, learning, preferences and costs it is not automatically a welfare gain.')
h('Sensitivity to baseline adjustment: A2020',True)
rows=[]
for y in P:
    a=one(policy,y);r=one(sens,y,specification='Baseline adjustment with assignment interactions')
    rows.append([lab(y),v(a['estimate'],m(y),d(y)),v(r['estimate'],m(y),d(y)),ci(r,y),r['n']])
table(['Outcome','Unadjusted','Adjusted','Adjusted 95% CI','N'],rows,[179,77,77,139,56])
para('Adjustment uses sex, recorded phone, baseline age and SES, mean imputation of missing baseline values with missingness flags, and assignment interactions. Covariates are centered within the target cohort. No follow-up age, parental reports, receipt, school choice or work variables are controls. This is a comparability/precision check, not a replacement for random assignment.')
para('A broader correction across all nine outcomes is reported in the CSVs. It leaves no policy-five test significant at 5%; private attendance and highest grade remain significant, while repetitions do not. Targeted exclusions and HC3 checks appear later. A flag is not an automatic error, and records are never removed merely to improve significance.')
para('<b>Policy implication:</b> the data support increased private attendance and suggest less work time, but do not establish broad improvement across the five outcomes or provide enough information for cost-effectiveness or scale-up recommendations.')

# Page 5: schooling and first stage.
page('4. Schooling outcomes and instrument relevance')
table(['A2020 outcome','Control mean','Effect','95% CI','Raw p','Holm p','N'],effects(school,S,mean=True),[142,63,61,117,47,49,49])
para('The four retained schooling outcomes form their own Holm family. Grade completion and repetition describe progression; they remain complementary to the prioritised policy outcomes. Current private attendance is both a policy response and the proposed IV first stage.',True)
h('Lottery effects on private schooling',True)
rows=[]
for c in ['A2020','A2022','B2018']:
    for y in ['started_g6_private','started_g7_private','in_private_now']:
        r=one(first,y,c);rows.append([c,L[y],v(r['estimate'],100,2),ci(r,y),v(r['F_statistic'],1,1),r['n']])
table(['Cohort','Private-school measure','Effect (pp)','95% CI (pp)','Robust F','N'],rows,[62,154,71,119,67,55])
para('A2020 current private attendance averages 53.75% in controls and 69.66% in selected applicants. Control attendance shows two-sided uptake: applicants may pay privately using other resources. Current aid is not equivalent to assignment or verified program receipt.')
para('A2022 has a negative G6 point estimate but positive G7/current estimates. Sampling uncertainty and treatment definition matter. A positive first stage supports relevance but does not prove exclusion or no defiers. Each IV outcome below recomputes its first stage on that outcome\'s complete-case sample; the table above uses all observed responses for the schooling measure.')

# Page 6: exits and defiers.
page('5. Observed exits from private schooling')
para('An observed G6-to-current exit has started_g6_private = 1 and in_private_now = 0. The denominator includes G6-private applicants with current status observed. Missing current status stays unknown. G6 private attendance is itself post-allocation, so conditioning on it changes group composition: the exit-rate comparison is descriptive, not causal.')
table(['Cohort / arm','G6 private, status observed','Current nonprivate','Exit rate','Still enrolled','Not enrolled'],[['A2020 control',498,208,'41.77%',127,81],['A2020 selected',552,150,'27.17%',68,82],['A2022 control',115,32,'27.83%',25,7],['A2022 selected',126,11,'8.73%',8,3],['B2018 control',38,13,'34.21%',9,4],['B2018 selected',70,20,'28.57%',7,13]],[116,105,86,63,79,79])
para('Current-status unknown among G6-private applicants (control / selected): A2020 5 / 2; A2022 0 / 1; B2018 0 / 1. All observed exits have current enrollment observed. Current enrollment outside private school is consistent with switching sector; nonenrollment may reflect withdrawal or completion, so it is not automatically called dropout.',True)
table(['Selected A2020 ID','G6 / G7 / current private','Current enrollment','Handling'],[['100031','1 / 1 / 0',1,'Retain: currently enrolled nonprivately'],['100036','1 / 0 / 0',0,'Retain: reason for nonenrollment unknown'],['100062','1 / 0 / 1',1,'Retain reported return pattern'],['100203','1 / 1 / unknown','unknown','Current transition remains unknown'],['100449','1 / 1 / unknown',1,'Enrollment does not resolve school sector']],[97,137,92,202])
para('A2020 has 60/554 selected G6-private students reporting no private G7 start, versus 125/503 controls. G7 = 0 can include applicants who never reached G7. The 1/0/1 pattern occurs 23 times overall (seven selected A2020); exact transition dates and reasons are unavailable. A broader definition, private in G6 or G7 then nonprivate currently, finds 439 exits, including 184 selected applicants. It differs from the G6-only table.')
para('<b>These are not identified defiers.</b> A defier would be private without an offer but nonprivate with one at the same defined time. Only one of those counterfactual choices is observed. Leaving, renewal failure, returning to private school or a positive average first stage cannot classify individual compliance types. All matching IDs and original histories remain in the transition audit.')

# Page 7: ATT distinction.
page('6. ATT depends on what treatment means')
para('An average treatment effect on the treated (ATT) requires a precise treatment definition. An offer, actual subsidy receipt and private schooling are different treatments.')
table(['Treatment','Target','What can be identified'],[['Lottery offer Z','Effect among applicants offered the subsidy','Under random assignment, offer ATT equals the offer ATE in expectation. The policy ITT estimates this offer effect.'],['Actual program receipt S','E[Y(1) - Y(0) | S = 1]','Not identified here: program-specific take-up and renewal histories are missing, and recipients select into use and retention.'],['Private schooling D','Effect among all privately schooled applicants','Not generally identified by offer IV. Always-takers attend privately under either assignment, and their schooling effects are unidentified.']],[116,136,276])
h('Why current aid does not identify recipient ATT',True)
para('Recipients can differ in family resources, preferences, access and academic performance. Renewal depends on progress, so current receipt may result from earlier outcomes. A comparison of recipients and nonrecipients, even with observed controls, does not automatically estimate ATT.')
para('receiving_aid_now denotes <b>any subsidy or scholarship in the survey year</b>: 56.25% among A2020 selected applicants and 5.53% among controls. It is not a verified initial-receipt or renewal history for this program. Dividing the ITT by this any-aid difference and calling it program-recipient ATT is unsupported.')
h('When a recipient-IV could equal recipient ATT',True)
para('With verified program-specific receipt, one-sided noncompliance S(0) = 0, exclusion and the other IV assumptions, all recipients are compliers. The local recipient effect then coincides with recipient ATT. These conditions cannot be established using the supplied any-aid field; access by controls or time-varying receipt would change the interpretation.')
para('For private schooling, substantial control uptake demonstrates that compliance is two-sided. Under standard IV assumptions, the ratio is a LATE for applicants whose private attendance changes because of the offer. It is not the average effect for all privately schooled applicants or all subsidy recipients.')
h('Needed to move beyond discussion',True)
para('Obtain program-specific initial receipt, annual disbursements and renewal dates; verify whether controls can access this program; define treatment as any receipt, amount or duration; and justify exclusion for that definition. Until then, a numerical program-recipient ATT would imply information the files do not contain.')

# Page 8: IV specification and identification.
page('7. Instrumenting private schooling with the offer')
para('<b>Instrument:</b> Z = selected in the lottery. <b>Endogenous treatment:</b> D = in_private_now. Estimate the five outcomes separately within each cohort. Current aid use is a realised follow-up variable and is not the instrument.')
para('<b>First stage:</b> D = alpha_D + pi Z + v.<br/><b>Reduced form:</b> Y = alpha_Y + rho Z + e.<br/><b>Just-identified 2SLS:</b> beta_IV = rho / pi.')
para('For each outcome, all three calculations use the identical applicants with observed Y and D. The main policy ITT uses all observed Y and can differ from this reduced form. Never divide a full-outcome ITT by a first stage from a different sample.')
table(['Assumption','Assessment'],[['Random assignment','Maintain the documented within-cohort lottery; inspect baseline balance and obtain the complete roster and procedure.'],['Relevance','Report the same-sample first-stage effect and robust F. Strength does not validate the remaining assumptions.'],['Exclusion','The offer must affect the outcome only through the defined private-school treatment. Fee relief, renewal incentives and earlier schooling threaten this condition.'],['Monotonicity','At the same defined time, no applicant attends privately only without an offer. Observed transitions cannot identify these counterfactual types.'],['No interference / defined treatment','Peer, capacity and spillover effects are unmeasured; the meaning of private-school treatment must be coherent.']],[124,404])
para('<b>Exclusion is demanding for a current snapshot.</b> The subsidy can free household resources or encourage effort without changing current sector. Prior private schooling and duration may affect cumulative years, work and family outcomes even when current attendance is the same. Some outcomes may precede the current attendance decision. The resulting private-school interpretation is therefore exploratory and conditional.')
para('The robust ratio variance retains the joint covariance of reduced form and first stage. Ordinary second-stage OLS standard errors are incorrect. Anderson-Rubin (AR) sets invert the HC2/t test of Y - beta D on assignment and allow bounded, disjoint or unbounded sets. This is asymptotic robust inference, not an exact randomization test. LATE identification follows Angrist, Imbens and Rubin (1996); references appear on the final page.')

# Page 9: A2020 IV estimates.
page('8. A2020 private-school IV results')
rows=[];samples=[]
for y in P:
    r=one(iv,y,baseline_adjusted='FALSE');rows.append([lab(y),v(r['estimate'],m(y),d(y)),ar(r,y),p(r['ar_p_zero']),p(r['holm_ar_p']),r['n']])
    samples.append([L[y],v(r['reduced_form'],m(y),d(y)),v(r['first_stage'],100,2),v(r['first_stage_F'],1,2),r['n_control'],r['n_selected']])
table(['Outcome','IV effect','95% robust AR set','AR p','AR Holm p','N'],rows,[151,75,144,55,56,47])
para('Binary effects and sets are percentage points; other units are years and hours/week. AR p tests a zero effect; Holm covers the five A2020 IV outcomes. Sets are individual, not simultaneous. Conventional robust 2SLS intervals are included in the machine-readable tables.',True)
h('The matched samples behind each ratio',True)
table(['Outcome','Reduced form','First stage (pp)','Robust F','Control N','Selected N'],samples,[159,85,88,66,64,66])
para('Reduced forms use years, percentage points for binary outcomes, or hours/week; all first stages use percentage points. For school years, the matched reduced form is about 0.079 and the first stage about 0.160, yielding 0.497 years. The policy ITT of 0.093 uses more observed outcomes and must not be substituted into that ratio.')
para('None of the five IV tests survives multiplicity adjustment. Weekly hours has an AR set excluding zero before adjustment, but its Holm p is about 0.158. The sizeable point estimate is not an established private-school effect. A2020 first-stage F values of about 32 do not validate exclusion or monotonicity.')
h('Baseline-adjusted IV check',True)
r=one(iv,'hours_worked',baseline_adjusted='TRUE')
para(f"With additive pretreatment controls, the weekly-hours IV estimate is {v(r['estimate'],1,3)}, with AR set {ar(r,'hours_worked')}. This set includes zero, reinforcing the uncertainty. Unlike the assignment-interacted policy adjustment, this IV check uses additive controls in the instrument and outcome equations.")
para('If the IV assumptions hold, the effect applies to applicants whose current private attendance is induced by the offer. It does not generalize to all private-school students, subsidy recipients or municipal residents. The histories and financial-support mechanisms limit a literal current-private LATE interpretation.')

# Page 10: cohort policy checks.
page('9. Separate checks in A2022 and B2018')
para('A2022 is a newer cohort in the same municipality; B2018 is an older cohort elsewhere. Age and schooling patterns are consistent with shorter/longer exposure, but dates are absent. Comparisons also mix applicant age, composition, calendar time and municipality; they cannot isolate duration or place effects.')
for c in ['A2022','B2018']:
    h(c+': five policy offer effects',True)
    table(['Outcome','Effect','95% CI','Raw p','Holm p','N'],effects(policy,P,c),[171,77,129,52,52,47])
para('<b>A2022 has no observed marriage/cohabitation or parenthood events in either arm.</b> The descriptive difference is zero, but this is not a precisely estimated zero population effect. Conventional robust SEs collapse, so their confidence intervals and p-values are not reported.')
para('Smaller samples and different event prevalence limit these checks. A difference in significance does not establish a difference in effects. B2018 also has baseline imbalances. The separate cohorts provide context for the A2020 analysis, not clean estimates of elapsed-time or municipality effects.')

# Page 11: other cohort IV and alternative exposures.
page('10. IV checks across cohorts and exposures')
for c in ['A2022','B2018']:
    h(c+': current-private IV',True)
    rows=[]
    for y in P:
        r=one(iv,y,c,baseline_adjusted='FALSE');rows.append([lab(y),v(r['estimate'],m(y),d(y)),ar(r,y),v(r['first_stage_F'],1,2),r['n']])
    table(['Outcome','IV effect','95% robust AR set','First-stage F','N'],rows,[160,77,159,80,52])
para('First stages are weaker in these samples: roughly F = 8 in A2022 and F = 6 in B2018. Unrestricted approximate IV sets can extend beyond the logical +/-100 pp range for binary causal effects; these are not probability predictions. Their width indicates weak information. Zero-event A2022 outcomes have no reported inferential AR set.',True)
h('Alternative treatment definitions',True)
para('The package also instruments private starts in G6 and G7, with matched samples for each outcome. These indicate different exposures and potentially different compliers, so their ratios are sensitivity checks rather than interchangeable estimates. In A2020 the G6 first stage is much smaller than G7/current attendance.')
para('A2022 G6 has a weak negative point first stage. Its ratio should not be interpreted as the same positively induced complier effect without defending a coherent monotonicity direction. Earlier measures do not automatically solve exclusion because the offer changes resources, duration and renewal incentives beyond one binary school measure.')

# Page 12: broad data audit.
page('11. How the data were checked and handled')
para('I inspected raw tokens, types, distinct values, ranges, missingness, nonfinite values, fractional integer fields and common sentinels; checked duplicate/missing IDs and exact merge coverage; compared dictionary domains; tabulated missingness by cohort and assignment; and checked cross-field consistency. All original columns remain unchanged.')
table(['Finding','Count / scope','Handling'],[['Missing / duplicate / unmatched IDs','0 / 0 / 0','One-to-one merge; retain 1,618 applicants.'],['Invalid documented codes / sentinels','None detected','No blanket recoding, winsorization or outlier deletion.'],['Dictionary month mismatch','interview_month vs survey_month','Keep actual field name; document assumed alias.'],['Baseline age / SES missing','64 / 279','Preserve NA; adjustment uses explicit imputation and flags.'],['Neighborhood missing','721','All A2022/B2018 plus 279 A2020; omit from main controls.'],['Age change outside +2 to +4','350 / 1,549 observed pairs','Timing review flags; not 350 verified errors or an exclusion rule.'],['Age declines','11','Print IDs; preserve raw ages; mark age derivative missing.'],['Grade completion conflicts','14 applicants','Retain reports; targeted exclusion sensitivity.'],['Parent no older than child','5 cells','Only affected parent-age derivative becomes missing.'],['No work, positive hours','1 applicant','Retain reports; targeted exclusion check.'],['Working, zero weekly hours','32 applicants','Retain zeros; reference periods/absence may explain them.']],[168,115,245])
para('The issue ledger records ID, cohort, assignment, raw values, rule, severity and handling. Counts overlap and cannot be summed into unique exclusions. Missing outcomes are never filled with zero. Zero parental schooling and work hours remain valid reported values unless other evidence contradicts them.')
para('ID <b>100538</b>, an A2022 control, reports highest grade 4 despite a private G6 start. The dictionary gives no explicit highest-grade range: preserve grade 4, flag the entry-history concern and check exclusion. Baseline grade and source questionnaires are needed to resolve it. The case lies outside the revised primary cohort.')

# Page 13: timing and years in school.
page('12. Age timing and school-year definitions')
para('The study describes follow-up approximately three years after application. I calculate survey age minus baseline age without assuming either field correct. There are 64 missing baseline ages, six missing survey ages and one overlap: 1,549 comparable pairs and 69 unknown pairs. The +2 to +4 window allows rough timing and birthdays but is a diagnostic screen only.')
table(['Cohort','Age pairs','Mean change','Median','Outside +2 to +4','Declines'],[[r['cohort'].replace('_',' '),r['age_pairs'],v(r['mean_age_change'],1,2),v(r['median_age_change'],1,0),r['age_outside_2_to_4'],r['age_decreased']] for r in cohort],[84,86,95,61,115,87])
fp=ROOT/'results/figures/age_changes.png'
if fp.exists():story.extend([Image(str(fp),width=528,height=201),Spacer(1,5)]);md.append('![Age-change distributions](../results/figures/age_changes.png)\n')
para('Application year plus age change is 2022 or 2023 for 1,477/1,549 pairs (95.4%). This is consistent with a common survey period but is an inference from ages, not an observed interview year. Exact elapsed time cannot be recovered.',True)
table(['Cohort','School-years N','Mean','Modal value (N)','Values above 4'],[['A2020',1171,'3.655','4 (875)',47],['A2022',275,'2.062','2 (235)',1],['B2018',164,'5.201','6 (116)',128]],[90,105,80,135,118])
para('The dictionary defines years_in_school as school years completed since allocation. There are 176 values above four; 718 exceed age change plus one; 18 are below highest grade minus five, a screen assuming grade 5 completed at entry. Dates, accounting conventions or age errors may explain these flags. Retain reported values; do not cap at three or discard B2018\'s longer histories.')
para('The requested school-years outcome remains primary and is not silently replaced with highest grade. Keep its measurement caveat beside the estimate and use grade/repetition as complementary evidence.')

# Page 14: exact age records.
page('13. The 11 decreasing-age records')
table(['Applicant ID','Cohort','Selected','Baseline age','Survey age','Change'],[[r['applicant_id'],r['cohort'].replace('_',' '),r['selected'],v(r['age_at_application'],1,0),v(r['age_at_survey'],1,0),v(r['age_change'],1,0)] for r in neg],[97,94,71,93,93,80])
para('ID <b>100368</b> in A2020 changes from 15 to 10; ID <b>100910</b> in A2022 from 17 to 13. These are inconsistent age pairs. Unique matching IDs do not reveal whether baseline age, survey age or another record field is wrong. No reliable correction can be inferred.')
para('<b>Handling:</b> preserve both original age columns and all outcomes. age_at_survey_clean becomes missing for these 11 applicants, marking unusable chronology rather than asserting survey age caused the discrepancy. Primary outcomes do not control for age. The adjusted check uses reported baseline age and a separate exclusion sensitivity.')
para('One negative-age case is A2020 and ten are A2022; none is B2018. The revised A2020 age-exclusion sensitivity removes only the relevant one applicant. Removing all 350 off-window records would disproportionately discard comparison cohorts and is not a main cleaning rule.')
h('Review files and unresolved chronology',True)
para('There are also 86 unchanged ages, concentrated in A2022. These may reflect timing or measurement issues and remain flagged and retained. age_review_records.csv contains all 419 unique applicants with missing age pairs or off-window changes, with raw ages, ID, cohort, assignment and flags.')
para('Age exclusions test sensitivity rather than repair the source data. Follow-up-based exclusions can change comparability. Birth dates, application/interview dates and source questionnaires are needed; setting survey age to baseline plus three would invent a correction.')

# Page 15: grade and household record details.
page('14. Grade, parent-age and work conflicts')
table(['Applicant ID','Cohort','Selected','Highest grade','Finished G6 / G7 / G8'],[[r['applicant_id'],r['cohort'].replace('_',' '),r['selected'],r['highest_grade'],' / '.join(v(r[f'finished_g{g}'],1,0) for g in [6,7,8])] for r in grade],[96,87,73,98,174])
para('All 14 report highest grade at least 6 and all three completion flags zero. Thirteen contradict all thresholds; ID 100734 contradicts G6 only. Nine are selected, five controls. No source establishes which field is authoritative. Retain direct reports, do not generate completion from disputed highest grade, and compare targeted exclusions.',True)
table(['Applicant ID','Child survey age','Flagged parent age','Clean derivative'],[['100389',14,'Mother 14','Mother age missing'],['100421',13,'Mother 8','Mother age missing'],['100659',16,'Father 1','Father age missing'],['100840',15,'Mother 15','Mother age missing'],['101329',16,'Mother 16','Mother age missing']],[98,112,140,178])
para('Two other parent-child gaps below 12 and three above 60 receive review flags without correction. Parent ages are not main controls. ID <b>100767</b> reports working = 0 but four weekly work hours: retain both and check exclusion. The 32 working applicants with zero weekly hours retain zero because reference periods or temporary absence may differ.',True)

# Page 16: sex differences and concrete sensitivities.
page('15. Sex differences and sensitivity checks')
para('The original girls-versus-boys question is retained. Estimate effects by sex within A2020 and test the direct contrast, boys minus girls. A significant estimate for one sex and insignificant estimate for the other is not evidence of different effects.')
rows=[]
for y in P+S:
    g=one(sex,y,sex='Girls');b=one(sex,y,sex='Boys');a=one(sex,y,sex='Boys minus girls')
    rows.append([lab(y),v(g['estimate'],m(y),d(y)),v(b['estimate'],m(y),d(y)),ci(a,y),p(a['holm_interaction_p'])])
table(['Outcome','Girls effect','Boys effect','Boys - girls 95% CI','Holm p'],rows,[170,77,77,145,59])
para('Holm adjustment uses separate five-policy and four-schooling families. Interaction intervals are individual. Small subgroup event counts limit precision; compare direct interactions rather than subgroup p-values.',True)
h('Targeted A2020 checks',True)
rows=[]
for spec,label in [('Exclude declining-age records','Exclude declining age'),('Exclude schooling contradictions','Exclude grade conflicts'),('Exclude work-hours contradiction','Exclude work/hours conflict'),('HC3 standard errors','HC3 uncertainty')]:
    yr=one(sens,'years_in_school',specification=spec);hr=one(sens,'hours_worked',specification=spec)
    rows.append([label,v(yr['estimate'],1,3),yr['n'],v(hr['estimate'],1,3),ci(hr,'hours_worked')])
table(['Specification','Years effect','Years N','Hours effect','Hours 95% CI'],rows,[169,74,58,80,147])
para('These checks retain the source data and make exclusions explicit. Excluding a post-assignment inconsistency can alter the observed population and is not a repair. No specification should be chosen simply because its p-value crosses 0.05. The full CSV contains every retained and policy outcome.',True)

# Page 17: missing-data bounds and implementation.
page('16. Missingness bounds and reproducibility')
para('Logical bounds put all missing selected outcomes at the minimum and missing control outcomes at the maximum, then reverse the assignment. They use known binary support [0,1], retain the original cohort denominators and leave observed outcomes unchanged.')
table(['A2020 binary outcome','Lower bound (pp)','Upper bound (pp)','Missing selected','Missing control'],[[L[y],v(one(bounds,y)['lower'],100,2),v(one(bounds,y)['upper'],100,2),one(bounds,y)['missing_selected'],one(bounds,y)['missing_control']] for y in ['married_or_cohab','has_child','working','in_school_now','in_private_now']],[178,99,99,78,74])
para('<b>These are identification bounds, not confidence intervals.</b> They address unknown responses conditional on the observed sample, not assignment uncertainty or incorrect observed values. An all-negative missingness bound for an outcome whose robust interval includes zero is not a contradiction. Observed maxima for school years/hours are not established outcome supports, so no arbitrary finite bounds are asserted for them.')
h('Reproduce the analysis',True)
para('Run <b>Rscript code/run_analysis.R</b> from the extracted package, or give its full path. The script uses base R and resolves relative paths; no personal-path changes are required. It regenerates derived data, ledgers, tables and figures. The annotated code/run_analysis.md explains the code. The optional PDF builder uses Python and ReportLab.')
table(['Location','Purpose'],[['data/raw/','Unmodified supplied CSVs and dictionary.'],['data/derived/','All original fields, clean derivatives, flags and exact issue IDs.'],['results/tables/revised_*.csv','Authoritative cohort-specific policy, schooling, IV, balance and robustness estimates.'],['revision_transitions_qc/','Independent history audit, exact exit IDs and denominators.'],['revision_iv_qc/','Independent ITT/IV implementation and methods checks.'],['report/ and presentation/','Editable report, PDF and PowerPoint draft.'],['documentation/','Sources, methods, raw hashes and AI-use record.']],[192,336])
para('Independent checks reproduce transition counts and the IV ratio/covariance calculations. A one-to-one merge, unchanged raw files and successful execution validate implementation, not random assignment, exclusion, measurement accuracy or generalizability.',True)

# Page 18: conclusions, questions, citations.
page('17. What would strengthen the conclusion?')
para('<b>Allocation:</b> obtain the eligible roster, priority groups, lottery probabilities and assignment-unit rules. This would clarify the maintained complete-randomization assumption, B2018 balance concerns and household or school dependence.')
para('<b>Timing and measurement:</b> obtain birth dates, application and interview dates, the survey year, the school-year counting convention and original questionnaires. Resolve the printed age/grade/work conflicts from source records rather than assumed corrections.')
para('<b>ATT and mechanisms:</b> request program-specific receipt, disbursement, renewal and private-school histories. Clarify whether nonselected applicants can access the same program. Current any-aid use cannot replace these records.')
para('<b>Policy scale and welfare:</b> costs, learning, earnings, household/school links and later outcomes are needed to assess cost-effectiveness, peer/capacity effects and welfare. Less paid work alone does not establish a welfare improvement. Estimates apply to these lottery applicants and recorded horizons; they do not automatically generalize to all residents or a universal rollout.')
h('Study and methodological sources',True)
para('Study facts and definitions: DIL Canvas assessment viewed September 22, 2026; study_baseline.csv, study_followup.csv and data_dictionary.csv. A2020 prioritization follows the applicant\'s clarification. All empirical estimates are calculated from the supplied files.',True)
para('Angrist, Imbens and Rubin (1996), <link href="https://users.nber.org/~rdehejia/%21%40%24AEM/Topic%2004%20IV/readings/angrist_imbens_rubin_JASA_1996.pdf" color="#087E8B">Identification of Causal Effects Using Instrumental Variables</link>, for LATE and compliance assumptions. Imbens (2014), <link href="https://www.nber.org/papers/w19983.pdf" color="#087E8B">Instrumental Variables: An Econometrician\'s Perspective</link>, for identification and interpretation.',True)
para('Robust variance: <link href="https://declaredesign.org/r/estimatr/articles/mathematical-notes.html" color="#087E8B">estimatr mathematical notes</link>. Baseline adjustment: <link href="https://arxiv.org/abs/1208.2301" color="#087E8B">Lin, Agnostic notes on regression adjustments to experimental data</link>. Multiplicity: <link href="https://stat.ethz.ch/R-manual/R-devel/library/stats/html/p.adjust.html" color="#087E8B">R p.adjust documentation</link>. Weak-IV inference: <link href="https://economics.mit.edu/sites/default/files/publications/thirdsubmission.pdf" color="#087E8B">Mikusheva, Robust Confidence Sets in the Presence of Weak Instruments</link>. These sources support methods, not the program\'s empirical results.',True)
para('<b>Draft status:</b> nothing has been uploaded or submitted. The applicant should review the analysis and assumptions, make revisions and add the final chat PDF plus its public link. The AI-use note does not replace those required artifacts. Submission remains with the applicant.')

def footer(canvas,doc):
    canvas.saveState();canvas.setStrokeColor(colors.HexColor('#D5DFE5'));canvas.line(42,35,570,35)
    canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#526575'))
    canvas.drawString(42,23,'DIL assessment | A2020 primary | Revised draft for review');canvas.drawRightString(570,23,str(doc.page));canvas.restoreState()
doc=SimpleDocTemplate(str(OUT/'DIL_analysis_report.pdf'),pagesize=(612,792),rightMargin=42,leftMargin=42,topMargin=39,bottomMargin=46,title='Government subsidies, schooling and life outcomes - A2020 primary',author='AI-assisted analysis for applicant review')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(OUT/'DIL_analysis_report.md').write_text('\n'.join(md),encoding='utf-8')
print(OUT/'DIL_analysis_report.pdf')
