"""Create the 24-slide companion from focused, raw-data-generated result tables.
Run after: Rscript code/slide_regressions.R
Requires Python standard library + reportlab; paths resolve from this script.
Does not edit the detailed audit report, raw data or the presentation.
"""
from pathlib import Path
import csv, html, math, re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'report';OUT.mkdir(exist_ok=True)
SRC=ROOT/'results/slide_regressions'
def load(name):
    with (SRC/(name+'.csv')).open(newline='',encoding='utf-8-sig') as f:return list(csv.DictReader(f))
T={name:load(name) for name in ['itt','first_stages','policy_sensitivity','iv','sex','age_effects','age_heterogeneity','age_groups','fe_itt','fe_iv','fe_category_counts','cohort_summary','audit_counts','transitions','record_examples','policy_missingness','balance_permutation']}
P=['years_in_school','married_or_cohab','has_child','working','hours_worked'];S=['in_school_now','in_private_now','highest_grade','total_repeats']
B={'married_or_cohab','has_child','working','in_school_now','in_private_now'}
L={'years_in_school':'School years since allocation','married_or_cohab':'Married / cohabiting','has_child':'Has a child','working':'Doing paid work','hours_worked':'Weekly work hours','in_school_now':'Currently enrolled','in_private_now':'Currently private','highest_grade':'Highest grade completed','total_repeats':'Grade repetitions'}
G=['10-11','12-13','14-18']
def norm(c):return c.replace('_','')
def one(name,y=None,c='A2020',**filters):
    rr=[r for r in T[name] if (y is None or r.get('outcome')==y) and ('cohort' not in r or norm(r['cohort'])==norm(c)) and all(r.get(k)==str(v) for k,v in filters.items())]
    if len(rr)!=1:raise ValueError((name,y,c,filters,len(rr)))
    return rr[0]
def finite(x):
    try:return math.isfinite(float(x))
    except (ValueError,TypeError):return False
def v(x,mult=1,dec=2):
    if not finite(x):return 'NR'
    z=float(x)*mult
    if abs(z)<.5*10**(-dec):z=0
    return f'{z:.{dec}f}'
def p(x):return ('<.001' if float(x)<.001 else f'{float(x):.3f}') if finite(x) else 'NR'
def mult(y):return 100 if y in B else 1
def digits(y):return 1 if y in B else 2 if y=='hours_worked' else 3
def effect(r):return v(r['estimate'],mult(r['outcome']),digits(r['outcome']))
def label(y):return L[y]+(' (pp)' if y in B else '')
def ci(r):
    y=r['outcome']
    return f"[{v(r['ci_low'],mult(y),digits(y))}, {v(r['ci_high'],mult(y),digits(y))}]" if finite(r['ci_low']) and finite(r['ci_high']) else 'NR'
def ar(r):
    y=r['outcome']
    if r['ar_type']=='bounded':return f"[{v(r['ar_low'],mult(y),digits(y))}, {v(r['ar_high'],mult(y),digits(y))}]"
    return re.sub(r'(?<![A-Za-z])[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?',lambda m:v(m.group(),mult(y),digits(y)),r['ar_set'])
def ivrow(y,exposure='in_private_now',adjusted='FALSE'):return one('iv',y,exposure=exposure,baseline_adjusted=adjusted)
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='Body',fontName='Helvetica',fontSize=9.5,leading=13.2,spaceAfter=8,textColor=colors.HexColor('#253746')))
styles.add(ParagraphStyle(name='Note',fontName='Helvetica',fontSize=8.1,leading=10.8,spaceAfter=6,textColor=colors.HexColor('#516573')))
styles.add(ParagraphStyle(name='Cell',fontName='Helvetica',fontSize=7.9,leading=10.3))
styles.add(ParagraphStyle(name='Head',fontName='Helvetica-Bold',fontSize=7.9,leading=10.2,textColor=colors.white))
styles['Heading1'].fontName='Helvetica-Bold';styles['Heading1'].fontSize=18;styles['Heading1'].leading=21.5;styles['Heading1'].spaceAfter=12;styles['Heading1'].textColor=colors.HexColor('#143448')
styles['Heading2'].fontName='Helvetica-Bold';styles['Heading2'].fontSize=11.6;styles['Heading2'].leading=14.8;styles['Heading2'].spaceAfter=6;styles['Heading2'].spaceBefore=7;styles['Heading2'].textColor=colors.HexColor('#087E8B')
story=[];md=['# Companion to the 24-slide presentation\n\nEvery section explains the corresponding slide in DIL_Assessment_Baseline.pptx. A2020 remains the main cohort, pooling all baseline ages.\n']
def plain(t):
    t=re.sub(r'<link href="([^"]+)"[^>]*>(.*?)</link>',r'[\2](\1)',t)
    return html.unescape(re.sub('<[^>]+>','',t.replace('<br/>',' ').replace('<b>','**').replace('</b>','**')))
def para(t,note=False):story.append(Paragraph(t,styles['Note' if note else 'Body']));md.append(plain(t)+'\n')
def h(t):story.append(Paragraph(t,styles['Heading2']));md.append('### '+plain(t)+'\n')
def slide(n,title,sources,chunks):
    if n>1:story.append(PageBreak());md.append('\n---\n')
    t=f'Slide {n} | {title}';story.append(Paragraph(t,styles['Heading1']));md.append('## '+t+'\n')
    para('Source: '+', '.join('results/slide_regressions/'+s+'.csv' for s in sources)+'.',True)
    para('Code: code/slide_regressions.R (identical executable chunks in .md), CHUNK '+chunks+'.',True)
def table(headers,rows,widths):
    assert sum(widths)==528
    data=[[Paragraph(html.escape(str(x)),styles['Head']) for x in headers]]+[[Paragraph(html.escape(str(x)),styles['Cell']) for x in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#143448')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#D5DFE5')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F3F6F8')])]))
    story.extend([t,Spacer(1,8)]);md.append('| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |')
    md.extend('| '+' | '.join(str(x).replace('|','\\|') for x in r)+' |' for r in rows);md.append('')
def itt_table(outcomes,c='A2020'):
    rows=[]
    for y in outcomes:
        r=one('itt',y,c);mm=mult(y);dd=digits(y)
        rows.append([label(y),v(r['control_mean'],mm,dd)+('%' if y in B else ''),v(r['treatment_mean'],mm,dd)+('%' if y in B else ''),effect(r),ci(r),p(r['p_value']),r['n']])
    table(['Outcome','Control group mean','Treatment group mean','Effect','95% CI','p','N'],rows,[143,61,61,52,116,45,50])
def standard_itt():
    para('<b>Model:</b> Y_i = alpha + tau Z_i + e_i, where Z = selected. With an intercept and no other controls, tau is the selected-minus-control observed mean. Each mean divides the observed Y sum by its arm\'s observed count; for binary Y, this is events/observations. Outcomes use separate samples. Full-applicant interpretation requires appropriate response assumptions; similar response rates alone cannot establish no missing-outcome bias.')
    para('<b>Uncertainty:</b> applicant-level HC2 covariance; SE(tau) = sqrt(s1 squared/n1 + s0 squared/n0) in this two-group model. The 95% interval is tau +/- t(.975, n-2) x SE. Two-sided raw p = 2 x Pr[t(n-2) &gt; |tau/SE|]. No cohort, school or neighborhood clustering is imposed. The lottery assumption and possible interference remain substantive qualifications.')
def units_note():
    para('Display rule: binary means x 100 are percentages; binary effects/intervals x 100 are percentage points. Binary values round to one decimal, weekly hours to two, school-year/grade/count measures to three; p-values round to three, with values below .001 shown as &lt;.001. Calculations and tests use full precision, so rounded arm means need not subtract exactly to the printed effect.',True)

slide(1,'School subsidies and youth outcomes',['cohort_summary'],'1, 13')
para('This companion explains how every table and chart in the current 24-slide deck is produced. Slides 1-15 form the main presentation and 16-24 the appendix. The original detailed audit report remains available as DIL_analysis_report.pdf; this document is a reproducible crosswalk to the slides, not a replacement for its broader audit.')
h('Population and treatment')
para('The main population is municipality A\'s 2020 lottery applicants. The main analysis pools every baseline age, including missing baseline age. A2022 and B2018 are separate contextual checks. Treatment group means selected in the lottery; it does not mean verified subsidy receipt, aid use or private attendance. The title and cohort labels are editorial framing, not estimated effects.')
table(['Cohort','Applicants','Not selected','Selected','Role'],[[r['cohort'].replace('_',' '),r['n'],r['control'],r['selected'],'Primary' if r['cohort']=='A_2020' else 'Separate check'] for r in T['cohort_summary']],[89,86,102,95,156])
h('One source for displayed results')
para('Run Rscript code/slide_regressions.R. The focused script reads only data/raw/study_baseline.csv and data/raw/study_followup.csv, validates IDs, merges one-to-one and writes 17 CSVs to results/slide_regressions/. It uses base R. Each companion section names the exact CSV, relevant row filters and code chunk. The supplied data dictionary and assessment provide definitions and study design, rather than outside numerical findings.')
para('Run python code/build_slide_report.py to regenerate this PDF and Markdown after the focused R script. This authoring step requires ReportLab. Paths resolve relative to the script; no personal paths are needed. Neither command uploads or submits the assessment.')
h('Scope of the new analyses')
para('The user confirmed baseline-age groups 10-11, 12-13 and 14-18 during this revision. They are not actual school-grade groups: baseline grade is unavailable and the program targets G6 entry. Additional controlled models use pretreatment covariates and separate SES/neighborhood category effects. They supplement, rather than replace, the pooled-age A2020 main results.')

slide(2,'The program and the study population',['cohort_summary'],'1, 13')
para('<b>Visual:</b> a descriptive design table. Applicants are counts of merged rows within municipality/application_year; offers are sums of selected = 1. No regression, p-value or confidence interval is used. The study description supplies the subsidy, G6 entry and promotion-based renewal facts.')
table(['Cohort','N','Offers','Controls','Observed age pairs','Mean age change','Median'],[[r['cohort'].replace('_',' '),r['n'],r['selected'],r['control'],r['age_pairs'],v(r['mean_age_change'],1,2),v(r['median_age_change'],1,0)] for r in T['cohort_summary']],[80,49,61,62,104,103,69])
para('<b>Age-change column:</b> compute age_at_survey - age_at_application only when both are observed. The slide\'s typical-change phrases summarise the dominant patterns: A2020 +2/+3; A2022 0/+1; B2018 +4/+5. Mean/median and comparable-pair counts above are generated by the focused script. Missing age pairs are excluded only from this descriptive calculation, never from the cohort totals.')
para('The main table\'s 1,176 A2020 applicants equal 593 selected + 583 controls. The comparable counts for A2022 are 146 + 131 = 277, and B2018 91 + 74 = 165. These lotteries can have different assignment rates; combining them without cohort handling would change the comparison. The main analysis avoids that by estimating A2020 alone.')
h('Interpretation and data limitations')
para('The approximately three-year follow-up in the study description and observed age patterns are not fully reconciled. No interview year or exact dates are supplied. An older/newer application cohort is a check consistent with longer/shorter exposure, but differences also mix calendar time, age, composition and municipality. This table cannot estimate a pure duration effect or a municipality effect.')
para('Unique matched records establish complete matching between the two supplied extracts. They do not verify the original lottery roster or population-wide follow-up. The target is applicants, not all municipal residents. The A2020 emphasis is the user\'s clarified focus and is not described as preregistered.')

slide(3,'Data checks preserve uncertain records',['audit_counts','cohort_summary'],'1, 13')
para('<b>Visual:</b> a count-and-handling table, not estimated treatment effects. All counts refer to the complete merged sample of 1,618, across all three cohorts. CHUNK 1 checks missing/duplicate IDs and equality of the two ID sets before merging; CHUNK 13 generates the displayed flags from original values.')
metrics={'matched_unique_ids':'Unique matched applicants','age_decreased':'Survey age below application age','age_outside_2_to_4':'Observed age change outside [2,4]','grade_conflict':'Highest grade conflicts with a completion flag','no_work_positive_hours':'Working = 0, weekly hours > 0','working_zero_hours':'Working = 1, weekly hours = 0','school_years_above_four':'School years since allocation > 4'}
table(['Flag / check','Count','Exact rule and interpretation'],[[metrics[r['metric']],r['count'],{'matched_unique_ids':'One-to-one validated join by applicant_id.','age_decreased':'Both ages observed; survey minus baseline < 0.','age_outside_2_to_4':'Both ages observed; change < 2 or > 4. Diagnostic, not a verified error.','grade_conflict':'For any g in 6,7,8: observed finished_g differs from 1(highest_grade >= g).','no_work_positive_hours':'Both fields observed. Retain originals; one-record exclusion check.','working_zero_hours':'Retain zero; status and hours can have different reference periods.','school_years_above_four':'Retain and flag; exposure timing and school-year counting are uncertain.'}[r['metric']]] for r in T['audit_counts']],[190,45,293])
para('The 11 age decreases are not the same as the 350 timing flags; the counts overlap. A2020 contributes one decrease and 16 off-window pairs; A2022 ten and 252; B2018 zero and 82. Flags do not sum to a number of distinct applicants to remove.')
para('<b>Handling:</b> keep raw ages, grade reports, work status and hours. Do not force ages to baseline +3, cap all school years at three, derive disputed completion flags from highest grade, convert missing outcomes to zero, or delete every flagged record. The displayed primary regressions retain reported outcomes and omit only that model\'s missing outcome. The two targeted exclusions shown later are explicit sensitivity checks.')
para('This focused script reproduces the displayed counts and examples. The separate full analysis/report contains the broader source-token, domain and parent-age audit; those additional checks are not silently claimed as outputs of this focused script.',True)

slide(4,'Is the comparison group credible?',['cohort_summary','balance_permutation','policy_missingness','itt'],'1-3, 13, 14')
para('<b>Judgment:</b> A2020 lottery non-winners are a credible no-offer comparison if the documented lottery was implemented as described and outcome observation remains comparable. The available baseline check is consistent with that design. It does not independently prove randomization, rule out unobserved differences or establish no missing-outcome bias.')
table(['Evidence','A2020 result','What it supports or limits'],[['Assignment design','1,176 applicants: 593 offers, 583 non-winners','Random offer assignment supplies the counterfactual; compare by assigned offer rather than realized school choice.'],['Joint baseline balance','Permutation p = 0.6038; Monte Carlo SE 0.0049','No unusual observed imbalance by this test. A nonrejection does not prove that allocation was random.'],['Matched extracts','Every A2020 applicant ID matches across the two supplied files','No unmatched record in these extracts. Original roster coverage and item response remain separate questions.']],[119,153,256])
para('<b>Balance calculation:</b> CHUNK 14 compares pretreatment sex, phone, age and SES with explicit missingness handling, drops constant fields, and uses a fixed-covariance Mahalanobis statistic. It draws 9,999 fixed-arm-count relabelings under the stated applicant lottery (seed 20260922). The source CSV contains the result already shown in the methods appendix; this new slide fits no new model.')
rows=[]
for y in P+['in_private_now']:
    r=one('itt',y);rows.append([L[y],str(583-int(r['n_control'])),str(593-int(r['n_treatment'])),r['n']])
table(['Outcome / IV treatment','Missing control','Missing selected','Observed N'],rows,[229,108,108,83])
para('Counts above are baseline arm totals minus each outcome-observed arm count in itt.csv; policy totals agree with policy_missingness.csv. The comparison still needs a suitable response assumption. Similar or small missingness does not establish absence of bias. IV additionally requires both Y and private status, so conditioning on observed D can change the sample.')
para('Private attendance by 53.8% of controls does not invalidate their role as a no-offer counterfactual. It does mean the lottery compares access to the offer, not all-private versus no-private schooling, and rules out one-sided schooling uptake for ATT identification. Retained age, grade and work inconsistencies are measurement limitations rather than reasons to reassign lottery status.')

slide(5,'Five policy outcomes in A2020',['itt'],'1-3')
para('<b>Regression equation:</b> Y_i = alpha + tau Z_i + e_i; tau is the A2020 offer effect. Z_i = selected.')
itt_table(P)
standard_itt()
para('<b>Row filters:</b> cohort = A_2020 and outcome in years_in_school, married_or_cohab, has_child, working, hours_worked. Assignment is observed for all applicants. Observed arm counts are 579 controls/592 selected for school years, working and hours; 578/591 for marriage and parenthood. Thus N is 1,171 or 1,169, not a common complete-case sample across outcomes.')
para('The five raw p-values are the displayed p column. CHUNK 3 also applies Holm to this five-outcome family (not preregistered). None passes familywise 5%; hours has raw p about .027 and Holm p about .137. Hours includes all observed applicants, including zeros and the flagged working=0/hours=4 case. Conditioning on employment would select on an outcome potentially affected by the offer.')
units_note()

slide(6,'School choice and progression in A2020',['itt'],'1-3')
para('<b>Regression equation:</b> Y_i = alpha + tau Z_i + e_i, fitted separately for each A2020 schooling outcome.')
itt_table(S)
standard_itt()
para('<b>Row filters:</b> cohort = A_2020, outcome in in_school_now, in_private_now, highest_grade, total_repeats. These are additional outcomes, not conditioning variables. Private attendance includes everyone with observed private status, rather than only those currently enrolled. Reported highest grade is retained despite unresolved completion-flag conflicts.')
para('The school-four Holm family is separate from the policy five and was chosen during revision. Private attendance, highest grade and repetitions pass the four-outcome adjustment. Under the broader combined-nine correction in holm_all_nine_p, private attendance and highest grade remain significant, while repetitions do not. The printed p-values are unadjusted.')
para('Highest_grade is the highest completed grade. Years_in_school is school years completed since allocation. Total_repeats is a count: a -0.065 effect is about 6.5 fewer repetitions per 100 offers, not a 6.5-pp change in a binary repetition rate. Overall enrollment remains imprecise.')
units_note()

slide(7,'Schooling effects for girls and boys',['sex'],'1, 2, 10')
para('<b>Equation above the table:</b> Y_i = alpha + tau Z_i + gamma male_i + delta (Z_i x male_i) + e_i. Girls (male=0) have effect tau; boys (male=1) have effect tau+delta; the directly tested difference, boys minus girls, is delta.')
rows=[]
for y in S:
    g=one('sex',y,sex='Girls');b=one('sex',y,sex='Boys');a=one('sex',y,sex='Boys minus girls')
    rows.append([label(y),effect(g)+' / '+p(g['p_value']),effect(b)+' / '+p(b['p_value']),p(a['p_value']),p(a['holm_interaction_p'])])
table(['Schooling outcome','Girls effect / p','Boys effect / p','Difference p','Holm p'],rows,[167,112,112,71,66])
para('<b>Source and sample:</b> reuse the four schooling outcomes in sex.csv, cohort=A_2020. No new models or subgroup choices are introduced. Each model uses all observed Y and the supplied pretreatment male indicator, irrespective of enrollment, private attendance, later grade or work. subgroup_n in the source CSV records girls/boys observed counts; n records the joint model sample.')
para('<b>Inference:</b> coefficient contrasts use applicant HC2 covariance and t(n-4) from the saturated assignment-by-sex model. Girls/boys cells show raw two-sided effect p-values. Difference p tests delta=0 directly. Holm adjusts these four interaction tests as a family selected during revision, not preregistered.')
para('The nominal enrollment interaction is p=.048, but its four-schooling Holm p=.192. None of the corrected schooling interactions rejects at 5%. Both sexes show increased private attendance; differences in their point estimates or separate significance levels do not establish different treatment effects.')
para('These results address whether schooling effects differ for girls and boys. The appendix on slide 20 reports all nine outcome-by-sex results, with the five policy interactions in a separate family. This page presents the four schooling outcomes.')
units_note()

slide(8,'Policy effects by age at application',['age_groups','age_effects','age_heterogeneity'],'1, 2, 11')
para('<b>Regression equation:</b> Within each baseline-age group g: Y_i = alpha_g + tau_g Z_i + e_i. Joint test: tau_10-11 = tau_12-13 = tau_14-18.')
para('<b>Visual:</b> a five-outcome table across the three confirmed baseline-age groups. The column headers show all applicants in each group, not the outcome-observed regression sample. Define groups using age_at_application only: 10-11, 12-13, 14-18. Missing age is not imputed into a subgroup.')
table(['Application-age group','Applicants','Controls','Selected'],[[r['age_group'],r['n'],r['n_control'],r['n_treatment']] for r in T['age_groups']],[186,114,114,114])
rows=[]
for y in P:
    cells=[]
    for g in G:
        r=one('age_effects',y,age_group=g);cells.append(effect(r)+'; p='+p(r['p_value'])+'; N='+r['n'])
    a=one('age_heterogeneity',y);rows.append([label(y)]+cells+[p(a['p_value']),p(a['holm_p'])])
table(['Outcome','Age 10-11','Age 12-13','Age 14-18','Joint p','Joint Holm'],rows,[132,99,99,99,49,50])
para('<b>Models:</b> within each observed baseline-age group, regress Y on an intercept and selected; use HC2 and t(n_group-2). The 56 missing-age applicants stay in the pooled main ITT but not these subgroups. ID 100368 stays in ages 14-18 using recorded baseline age 15 despite survey age 10; which age is wrong is unknown, so misclassification remains possible. No age reassignment or extra subgroup sensitivity is fitted. Follow-up grades could be treatment-affected; baseline age is not actual grade.')
para('<b>Direct equality test:</b> collect the three effects tau and their HC2 variances. Let L have rows (-1,1,0) and (-1,0,1). F = (L tau)\' [L diag(SE squared) L\'] inverse (L tau) / 2; reference F(2, sum N_group - 6). This tests equal effects, rather than comparing individual p-values. The youngest group has zero marriage/child events; those intervals, p-values and corresponding joint tests are NR. No available joint test rejects at 5%; school-years raw joint p = .077 and five-family Holm p = .385.')
units_note()

slide(9,'The offer increases private-school attendance',['first_stages'],'3, 4')
para('<b>Regression equation:</b> Within cohort c: D_i = alpha_c + pi_c Z_i + v_i, where D = in_private_now. Robust first-stage F = (pi_c / SE_HC2(pi_c)) squared.')
para('<b>Chart:</b> grouped bars are 100 x the observed mean of in_private_now within each cohort/assignment arm. They show private attendance rates, not adjusted fitted values. <b>Table:</b> within-cohort selected-minus-control attendance differences, confidence intervals, robust F and raw p.')
rows=[]
for c in ['A2020','A2022','B2018']:
    r=one('first_stages','in_private_now',c);rows.append([c,v(r['control_mean'],100,1),v(r['treatment_mean'],100,1),effect(r),ci(r),v(r['F_statistic'],1,1),p(r['p_value']),r['n']])
table(['Cohort','Control %','Offer %','Effect pp','95% CI pp','F','p','N'],rows,[64,63,62,63,116,43,50,67])
para('<b>Numerators and denominators:</b> count private=1 separately in each arm and divide by the number with nonmissing private status. A2020 uses 573 controls and 590 selected, N=1,163; A2022 130/145, N=275; B2018 74/88, N=162. Missing private status is not an observed nonprivate outcome. Retain people with current enrollment=0 if private status is observed.')
para('<b>Model and tests:</b> D = alpha + pi Z + v separately by cohort; applicant HC2/t as on slide 5. The robust single-instrument F shown is (pi/SE(pi)) squared; it uses the same observed private-status sample as each bar pair and attendance regression. It is not an unadjusted homoskedastic textbook F.')
para('A2020 rises from 53.8% to 69.7%, a 15.9-pp first stage. A2022/B2018 first stages are less precise. Each later IV outcome recomputes its first stage on that outcome\'s common Y,D sample, so its F need not equal this table. Relevance alone does not establish exclusion, monotonicity or a causal schooling interpretation.')
units_note()

slide(10,'Private-school exits and monotonicity',['transitions'],'1, 13')
para('<b>Visual:</b> six descriptive fractions, combined into selected/control columns by cohort. This is a history tabulation, not a regression or a causal retention effect. The starting condition is started_g6_private=1; the ending field is in_private_now.')
rows=[]
for c in ['A2020','A2022','B2018']:
    for z in [1,0]:
        r=one('transitions',c=c,selected=z);rows.append([c,'Selected' if z else 'Control',r['exits'],r['paired_observed'],v(r['exit_fraction'],100,1)+'%',r['later_unknown'],r['exits_currently_enrolled'],r['exits_not_currently_enrolled']])
table(['Cohort','Arm','Exits','Denom.','Rate','Unknown','Enrolled exits','Not enrolled'],rows,[65,68,46,54,58,62,86,89])
para('<b>Denominator:</b> G6-private starters whose current private status is observed. <b>Numerator:</b> those applicants with current private=0. Missing current private status remains unknown and is excluded only from this fraction; it is never coded as an exit. The rate is numerator/denominator x100, rounded to one decimal. There is no uncertainty test on the slide.')
para('The 150 selected A2020 exits comprise 68 still enrolled nonprivately and 82 not currently enrolled. Nonenrollment could reflect withdrawal or completion and is not automatically called dropout. G6 private attendance is after the lottery; conditioning on it selects different sets of selected/control applicants. Therefore the difference between their exit rates is descriptive.')
para('<b>Not a test for defiers:</b> an IV defier has D(1)=0 and D(0)=1 at the same specified time. A past-to-current transition compares two dates under one realised offer status and cannot reveal both counterfactual choices. Renewal loss, changing school access or return to private school may explain histories, but program-specific receipt and transition dates are not observed.')

slide(11,'ATT for private-school attendees',['first_stages','iv'],'3, 4, 7-9')
para('<b>Treatment is private schooling:</b> D = in_private_now; the randomized subsidy offer Z = selected is the instrument. The target ATT_D = E[Y(1)-Y(0) | D=1] is the average effect of private schooling among current private-school attendees, where Y(d) denotes the outcome under schooling state d.')
r=one('first_stages','in_private_now')
table(['A2020 assignment','Observed private status','Currently private','Private attendance rate'],[['Not selected',r['n_control'],str(round(float(r['control_mean'])*int(r['n_control']))),v(r['control_mean'],100,1)+'%'],['Selected',r['n_treatment'],str(round(float(r['treatment_mean'])*int(r['n_treatment']))),v(r['treatment_mean'],100,1)+'%']],[129,129,133,137])
para('These are observed rates, not an ATT estimate: private=1 counts divided by observed private-status counts within each lottery arm. Missing private status is not zero. Current private attendance is 53.8% without an offer and 69.7% with an offer, so schooling uptake is two-sided. Controls choosing private school remain valid no-offer comparisons for the lottery ITT; they do not constitute a no-private-school comparison.')
h('Why the lottery IV is generally LATE, not ATT')
para('Under random assignment, relevance, exclusion, monotonicity and no interference, the offer-IV ratio identifies the average schooling effect for attendance compliers: D(1)=1 and D(0)=0. Under monotonicity, private-school controls are always-takers, while private-school lottery winners combine always-takers and compliers. Thus the full D=1 group contains people whose schooling is not shifted by the lottery.')
para('Conceptually, ATT_D is a weighted average of schooling effects for always-takers and the compliers who are actually private attendees under the offer allocation. IV identifies the complier effect but does not identify the always-taker effect. No homogeneity assumption equating those effects is imposed, and no numerical private-school ATT is reported.')
para('One-sided private-school uptake D(0)=0 would make all observed private attendees compliers, allowing LATE to equal ATT under the remaining assumptions. The observed control uptake rules out that special case here. A direct comparison of private attendees with nonattendees would be endogenous and is not a replacement for the lottery design.')
para('The current-attendance snapshot and possible direct resource/renewal effects still threaten the private-school exclusion restriction. The offer ITT stays the direct policy effect. This page defines the estimand and explains identification; it does not produce an additional regression or numerical ATT.')

para('Methodological source: <link href="https://www.math.mcgill.ca/dstephens/AngristIV1996-JASA-Combined.pdf" color="#087E8B">Angrist, Imbens and Rubin (1996), article and Rejoinder</link>, especially pp. 469-470 on always-takers, compliers and the additional conditions needed to recover ATT.',True)

slide(12,'Private-school IV estimates in A2020',['iv'],'1, 2, 7-9')
para('<b>Regression equation:</b> Reduced form: Y_i = alpha_Y + rho Z_i + e_i. First stage: D_i = alpha_D + pi Z_i + v_i. IV beta = rho/pi on the identical Y,D sample.')
rows=[]
for y in P:
    r=ivrow(y);rows.append([label(y),effect(r),ar(r),p(r['ar_p_zero']),p(r['holm_ar_p']),r['n']])
table(['Outcome','IV effect','95% robust AR set','AR p','Holm p','N'],rows,[148,69,148,54,55,54])
para('<b>Rows:</b> cohort=A_2020, exposure=in_private_now, baseline_adjusted=FALSE. For each Y, keep only observed Y, D and selected. School years/work/hours use 572 controls +590 selected =1,162; marriage/child use 572+589=1,161. Do not reuse the full-outcome ITT from slide 5.')
para('<b>Calculation:</b> regress Y and D separately on intercept+Z, retaining the same rows. Reduced form rho is the offer effect on Y; first stage pi is its effect on D. The just-identified IV coefficient is rho/pi. For school years, rho=0.079424 and pi=0.159897, giving 0.496720. This differs from dividing the 0.093069 full-outcome ITT by a separately estimated first stage.')
para('<b>AR inference:</b> for any proposed beta=b, test the selected coefficient in Y-bD on intercept+Z. Joint HC2 covariance gives variance Vrr-2bVrp+b squared Vpp. Retain b satisfying (rho-b pi) squared &lt;= t(.975,n-2) squared x that variance. CHUNK 7 solves this quadratic, allowing bounded, disjoint, half-line, all-real or empty sets. The displayed A2020 sets are bounded; this robust t inversion is asymptotic, not an exact lottery test.')
para('AR p is the two-sided test at b=0, equivalent to the matched-sample reduced-form test. Displayed p-values are raw; the five IV Holm values appear above and in the CSV. No IV outcome passes familywise 5%. Hours has raw AR p=.032, Holm=.158. Its baseline-adjusted set on slide 19 includes zero. Exclusion and monotonicity remain necessary regardless of the first-stage F.')
units_note()

slide(13,'Interpreting the IV estimates',['iv','first_stages'],'4, 7-9')
para('<b>Visual:</b> an assumptions panel rather than an additional estimated table. It interprets the same instrument Z=selected, current attendance D=in_private_now and five outcomes Y used on slides 9 and 12. The three named conditions are not measured binary fields and cannot be established from a fitted model alone.')
table(['Condition','How the data inform it','What remains unverified'],[['Relevance','The offer shifts current private attendance; slide 9 reports cohort estimates/F.','Strength differs by cohort and by IV outcome sample; F alone does not establish validity.'],['Exclusion','No direct statistical verification in this just-identified design.','Fee relief, family resources, renewal effort and earlier school history can affect Y beyond current D.'],['Monotonicity','Observed school histories and exits are tabulated on slide 10.','Each applicant reveals only D under the received assignment; individual defiers are not identifiable.']],[101,202,225])
para('Random assignment and no relevant interference are also required. If these conditions and a coherent binary schooling treatment hold, the Wald ratio is a local average effect among applicants who attend privately because they were offered the subsidy. It is not the average effect for every private-school student or all subsidy recipients.')
para('Current attendance is a snapshot. Cumulative school years, employment and family status can depend on prior private schooling or arise before the current attendance decision. A subsidy can change costs or effort even when current school sector stays unchanged. Thus the IV estimates are exploratory and conditional; the offer ITT remains the more direct policy estimand.')
para('Changing D to a private G6 or G7 start, as in slide 19, changes the treatment definition and possible complier group. These are not interchangeable doses of a single universal effect. A strong first stage or a narrow interval cannot fix exclusion or treatment-history problems.')
para('Methodological basis: Angrist, Imbens and Rubin (1996), Identification of Causal Effects Using Instrumental Variables; robust weak-instrument confidence-set inversion follows the test-inversion logic discussed by Mikusheva. These are methodological references, not external sources for the study\'s effect estimates.',True)

slide(14,'Separate checks in A2022 and B2018',['itt','balance_permutation'],'1-3, 14')
para('<b>Regression equation:</b> Within each cohort c: Y_i = alpha_c + tau_c Z_i + e_i, fitted separately for every outcome.')
para('<b>Visual:</b> a five-outcome table with one column for each cohort. Each cell reports its offer effect, raw HC2/t p-value and individual 95% interval. The A2020 column is reused from slide 5; no cohort pooling or duration regression is fitted.')
rows=[]
for y in P:
    cells=[]
    for c in ['A2020','A2022','B2018']:
        r=one('itt',y,c);cells.append(effect(r)+'; p='+p(r['p_value'])+'; N='+r['n'])
    rows.append([label(y)]+cells)
table(['Outcome','A2020 primary','A2022 check','B2018 check'],rows,[162,122,122,122])
standard_itt()
para('Filter municipality/application_year separately for each cohort. Missing Y is omitted only for that cell; controls are not pooled across lotteries. A2022 has no observed marriage/cohabitation or child events in either arm. The descriptive effect is zero, but SE/CI/p are NR because ordinary robust inference degenerates. This does not establish a zero population effect.')
para('Five-outcome Holm p-values are computed separately within each cohort, retaining family size five even when tests are NR. Printed slide cells show raw p-values. The B2018 balance warning comes from CHUNK 14\'s conditional permutation check, not these outcome regressions: p=.0152, rounded to .015. Slide 21 explains it.')
para('A2022/B2018 differ in application year, likely exposure duration, age/composition and, for B2018, municipality. A difference in significance is not a significant difference between effects. This table supports separate contextual checks, not an isolated causal duration or place comparison.')
units_note()

slide(15,'Policy interpretation',['itt','iv'],'3, 9')
para('<b>Visual:</b> summary text derived from the earlier A2020 tables. There is no new regression, composite index or welfare statistic. The paragraph about broader outcomes uses policy rows in itt.csv; the private-attendance paragraph uses its in_private_now row. The qualification about private-school causality uses the IV interpretation on slides 12-13.')
table(['Claim on the slide','Numerical basis','Interpretation'],[['Broader outcomes remain uncertain','No policy-five Holm p < .05. Hours raw p=.027; Holm=.137.','A suggestive direction is not established broad improvement or evidence of no effect.'],['Private attendance rises','15.9088 pp; HC2/t interval [10.3823,21.4354]; raw p < .001.','A clear offer response; supports relevance for the separate IV exercise.'],['Private-school effects require more','Hours IV raw AR p=.032; five-family Holm=.158; exclusion remains uncertain.','A valid lottery offer does not alone identify a private-school-only effect.']],[141,194,193])
para('The outcomes concern A2020 lottery applicants, pooled over baseline ages. The new age-group and controlled-model appendices do not change that main target. Main ITTs represent an offer under the observed take-up and renewal patterns, not a hypothetical program with universal receipt.')
para('Less paid work could permit more studying, but could also reduce income or reflect other changes. No learning scores, earnings, preferences, program costs or spillover estimates are in this slide. Therefore it makes no benefit-cost ratio, welfare claim, scale-up recommendation or municipality-wide impact estimate.')
para('The five-policy and four-schooling multiple-testing families were selected during revision, not preregistered. The combined-nine Holm sensitivity retains private attendance and highest grade but not grade repetitions. A concise main slide does not remove those qualifications, which are recorded in the speaker notes and the detailed report.')
para('No figure/table in this summary requires additional data handling: it reuses the outcome-specific missingness and retained-record decisions already described for slides 5, 6 and 12.')

slide(16,'Appendix 1: outcome definitions',['policy_missingness'],'1, 13')
defs={'years_in_school':'Number of school years completed since allocation','married_or_cohab':'Married or living with a partner at follow-up (0/1)','has_child':'Has at least one child at follow-up (0/1)','working':'Doing any paid work at follow-up (0/1)','hours_worked':'Hours worked per week at follow-up'}
table(['Raw variable','Dictionary meaning','Missing / 1,176'],[[y,defs[y],one('policy_missingness',y)['missing']] for y in P],[145,293,90])
para('<b>Count formula:</b> within the 1,176 A2020 applicants, missing = sum(is.na(Y)). The table is descriptive; no regression or test is required. The corresponding outcome-observed N is 1,176 minus this count. The two raw files are read with blank and NA tokens interpreted as missing; a reported numeric zero remains zero.')
para('<b>Definition source:</b> data/raw/data_dictionary.csv supplies the wording. years_in_school is years since allocation, not highest_grade and not total lifetime attainment. The main outcome is retained as supplied even though its counting convention and timing need clarification. Binary variables retain 0/1 coding for estimation and are multiplied by 100 only for presentation.')
para('<b>Hours:</b> include every observed hours response, including nonworkers and zeros. Do not replace missing hours with zero or condition the sample on working=1; work status can be affected by the offer. The working=0/hours=4 report is retained in the main estimates and tested through the one-record exclusion on slide 18.')
para('Counts are cohort-specific. Across all cohorts, school years/working/hours each have eight missing responses, marriage has eleven and parenthood twelve. These whole-data counts are not used as A2020 missing counts or sample denominators. Matching every ID between extracts does not eliminate item nonresponse or establish coverage of the original lottery population.')
para('IV additionally requires private status: a complete policy outcome with missing in_private_now remains in slide 5 and is omitted from that outcome\'s current-private IV. Baseline-age analyses additionally require observed application age; controlled models preserve missing baseline age through imputation and a missingness indicator.')

slide(17,'Appendix 2: specific records and handling',['record_examples'],'1, 13')
para('<b>Visual:</b> a selected record table, not an exhaustive list or regression sample. CHUNK 13 retrieves these six applicant IDs directly after the validated one-to-one merge, retaining their original values and assignment/cohort. They illustrate the rules without implying every flagged record appears on the slide.')
rows=[]
for r in T['record_examples']:
    i=r['applicant_id']
    observed={'100368':'Age '+r['age_at_application']+' -> '+r['age_at_survey'],'100044':'Age '+r['age_at_application']+' -> '+r['age_at_survey'],'100203':'Highest grade '+r['highest_grade']+'; finished G6/G7/G8 '+r['finished_g6']+'/'+r['finished_g7']+'/'+r['finished_g8']+'; current private missing','100767':'Working '+r['working']+'; weekly hours '+r['hours_worked'],'100031':'Private G6/G7/current '+r['started_g6_private']+'/'+r['started_g7_private']+'/'+r['in_private_now']+'; enrolled '+r['in_school_now'],'100062':'Private G6/G7/current '+r['started_g6_private']+'/'+r['started_g7_private']+'/'+r['in_private_now']}[i]
    action={'100368':'Keep raw values; exclude only in targeted A2020 age sensitivity.','100044':'Keep raw values; illustrates A2022 chronology, outside main A2020.','100203':'Keep unresolved grade. Current-private transition remains unknown.','100767':'Keep four hours; exclude only in targeted work-conflict sensitivity.','100031':'Keep as current private exit while still enrolled.','100062':'Keep history; not an identified defier.'}[i]
    rows.append([i,r['cohort'].replace('_',' '),r['selected'],observed,action])
table(['ID','Cohort','Offer','Original values','Handling'],rows,[58,64,39,188,179])
para('The two age examples decrease, but the data do not reveal which original age is wrong. A clean derivative in the full audit marks unusable chronology; it is not needed to reproduce the displayed focused regressions and does not overwrite raw ages. Age at survey is not a baseline control.')
para('ID 100203 reports a highest grade inconsistent with all three completion indicators and has unknown current private status. Do not infer its private status from prior attendance or school enrollment. It can remain in a policy model with observed Y while being excluded from the corresponding private-status IV.')
para('A 1/0/1 school history is not necessarily a verified leave-and-return sequence: a zero G7-private indicator can include never reaching G7. Neither that pattern nor a 1/1/0 exit identifies the unobserved counterfactual D(0),D(1) compliance type.')
para('The current deck\'s focused sensitivities reproduce age and work exclusions only. The broader detailed audit has additional grade-conflict checks and complete issue registers; do not mistake that broader analysis for another displayed focused regression.')

slide(18,'Appendix 3: primary sensitivity checks',['itt','policy_sensitivity'],'1, 2, 5, 6')
para("<b>Regression equation:</b> Primary/exclusions: Y_i = alpha + tau Z_i + e_i. Adjusted: Y_i = alpha + tau Z_i + Xc_i'gamma + Z_i Xc_i'delta + e_i.")
rows=[]
for y in P:
    a=one('itt',y);ss=[one('policy_sensitivity',y,specification=k) for k in ['Baseline adjustment with assignment interactions','Exclude declining-age records','Exclude work-hours contradiction']]
    rows.append([label(y),effect(a)+' / '+p(a['p_value'])]+[effect(r)+' / '+p(r['p_value']) for r in ss])
table(['Outcome','Primary effect / p','Adjusted effect / p','No age decline / p','No work conflict / p'],rows,[142,90,101,99,96])
para('<b>Primary column:</b> reuse cohort=A_2020 policy outcomes in itt.csv. <b>Age check:</b> exclude applicants with both ages observed and survey age below baseline age; only ID 100368 is removed from A2020. <b>Work check:</b> exclude working=0 and hours>0 when both are observed; ID 100767 is removed. Refit Y~selected separately for every Y in each altered sample. Preserve all other reported values, and do not recode hours.')
para('<b>Adjusted column:</b> use pretreatment male, phone, baseline age and SES with age/SES missingness flags. Replace missing age/SES by their mean over the full A2020 cohort, computed without outcome/assignment conditioning. Remove constant columns (phone is constant), center remaining controls at full-cohort means and fit Y = alpha + tau Z + Xc\'gamma + Z Xc\'delta + e. Tau is the adjusted contrast at the target mean covariates, not a raw group mean difference.')
para('Only missing Y is dropped after these baseline constructions. The original sample sizes are 1,171 or 1,169; each exclusion removes one observed-outcome record, giving 1,170 or 1,168. No 350-record broad timing exclusion is performed. The adjusted model preserves the original outcome samples.')
para('<b>Inference:</b> HC2/t with n minus the model rank degrees of freedom. The slide prints raw p-values, not newly adjusted p-values across the sensitivity specifications. Original main-family correction remains the reference; specifications are diagnostic checks, not additional discoveries chosen by significance. These numeric-SES, interacted controls differ from the additive category fixed effects on slide 23.')
units_note()

slide(19,'Appendix 4: additional IV specifications',['iv'],'5, 7-9')
para("<b>Regression equation:</b> Y_i = alpha_Y + rho Z_i + X_i'gamma_Y + e_i; D_i = alpha_D + pi Z_i + X_i'gamma_D + v_i; beta_IV = rho/pi. X is omitted in unadjusted rows.")
variants=[('Current attendance','in_private_now','FALSE'),('Current + baseline controls','in_private_now','TRUE'),('Private G6 start','started_g6_private','FALSE'),('Private G7 start','started_g7_private','FALSE')]
rows=[]
for title,exposure,adj in variants:
    r=ivrow('hours_worked',exposure,adj);rows.append([title,r['n'],v(r['first_stage_F'],1,1),p(r['first_stage_p']),effect(r),ar(r),p(r['ar_p_zero'])])
table(['Hours specification','N','FS F','FS p','IV hours','95% AR set','AR p'],rows,[138,44,46,46,62,143,49])
para('<b>Four rows only:</b> filter iv.csv to outcome=hours_worked and the exposure/adjustment pair above. CHUNK 9 fits the five main current-private IVs plus exactly these three additional hours specifications; it does not generate unshown alternatives for every outcome.')
para('Each row keeps common nonmissing hours, its chosen D and selected. Unadjusted rows use instrument-design matrix [1,Z]. The adjusted current-attendance row adds additive pretreatment controls from CHUNK 5: male, baseline age/SES imputations and their missing flags; phone is removed as constant. Unlike slide 18, there are no assignment-control interactions. There are also no SES/neighborhood category fixed effects; those are separate on slide 24.')
para('Compute matched reduced form rho and first stage pi using the same design matrix. IV=rho/pi. The first-stage F is (pi/SE_HC2(pi)) squared and its raw p tests pi=0. The robust AR p tests beta=0; invert the robust t test of Y-beta D on that design to get its set, with n-rank degrees of freedom. The full RF/FS covariance is retained. First-stage p and AR p answer different questions.')
para('G6, G7 and current attendance correspond to different school histories and possible compliers. Smaller G6 relevance magnifies the ratio and uncertainty. An adjusted current-attendance AR set that includes zero limits the main nominal hours finding; alternate exposure estimates are not evidence of one universal private-school effect. Exclusion remains demanding for all definitions.')
para('Hours and AR endpoints round to two decimals, F to one, p to three with &lt;.001. These sensitivity p-values are raw and do not define a preregistered new testing family. No age-group IV models are fitted or displayed.')

slide(20,'Appendix 5: effects for girls and boys',['sex'],'1, 2, 10')
para('<b>Regression equation:</b> Y_i = alpha + tau Z_i + gamma male_i + delta (Z_i x male_i) + e_i. Girls: tau; boys: tau+delta; difference: delta.')
rows=[]
for y in P+S:
    g=one('sex',y,sex='Girls');b=one('sex',y,sex='Boys');a=one('sex',y,sex='Boys minus girls')
    rows.append([label(y),effect(g)+' / '+p(g['p_value']),effect(b)+' / '+p(b['p_value']),p(a['p_value']),p(a['holm_interaction_p'])])
table(['Outcome','Girls effect / p','Boys effect / p','Difference p','Holm p'],rows,[167,112,112,71,66])
para('<b>Definition:</b> girls are male=0 and boys male=1 as supplied. Within A2020 and each observed Y, fit Y = alpha + tau Z + gamma male + delta (Z x male) + e. The table\'s girls effect is tau, boys effect tau+delta, and boys-minus-girls difference delta. These are direct linear contrasts of one saturated model, not comparisons of subgroup significance.')
para('<b>Inference:</b> apply the HC2 covariance to each contrast L: estimate=L\'b, variance=L\'V L. All use t(n-4) from the joint observed-outcome model. The CSV\'s subgroup_n gives the girls/boys observed counts, whereas n is the full model N. No school or employment response defines these pretreatment subgroups.')
para('Girls and boys cells print raw effect p-values. Difference p directly tests equal effects. Holm adjusts the five policy interaction tests and four schooling interaction tests separately. No corrected interaction rejects at 5%; the nominal enrollment difference p=.048 becomes .192 under its four-outcome family. An effect significant only for girls is insufficient evidence of heterogeneity.')
para('The supplied binary sex field determines these categories; the analysis does not infer unrecorded identities. Families and heterogeneity analyses were chosen during revision and are exploratory. Rare family outcomes and subgroup sizes limit precision.')
units_note()

slide(21,'Appendix 6: estimation and assignment checks',['itt','iv','balance_permutation'],'1-4, 7-9, 14')
para('<b>Visuals:</b> a side-by-side method table and three baseline-balance p-values. The method table describes the already fitted ITT and IV estimands; it does not fit another model. Its samples and uncertainty rules are those on slides 5 and 12.')
table(['Element','Offer effect','Private-school IV'],[['Coefficient','Observed selected minus control mean','Matched-sample outcome offer effect / school offer effect'],['Sample','Observed Y and Z','Identical observed Y,D,Z in both stages'],['Variance / inference','Applicant HC2; t(n-rank)','Joint HC2 RF/FS covariance; robust AR test inversion']],[102,213,213])
para('<b>Permutation balance construction:</b> within each cohort, use baseline male, phone, age and SES, with cohort-mean imputation and missingness indicators for age/SES; remove constant columns. Center X over the full cohort. Form V = (1/n_selected + 1/n_control) x cov(X), fixed across relabelings. The observed statistic is (mean X_selected - mean X_control)\' V inverse (that difference).')
para('Set seed 20260922. For each cohort in A2020,A2022,B2018 order, draw 9,999 assignment relabelings without replacement, each retaining its actual selected count. Recompute the statistic using the fixed X covariance. Report p=(1 + number simulated statistics at least observed)/(9,999+1). CHUNK 14 is a nonregression randomization diagnostic.')
table(['Cohort','Permutations','Balance p','Monte Carlo SE'],[[r['cohort'].replace('_',' '),r['permutations'],v(r['p_value'],1,4),v(r['monte_carlo_se'],1,4)] for r in T['balance_permutation']],[126,126,138,138])
para('The slide rounds p to three decimals: .604, .116, .015. A2020 phone is constant and excluded. Sparse-cell auxiliary Wald diagnostics are not substituted for these permutation results. The check assumes the stated fixed-count applicant lottery; it cannot verify its implementation. A rejection can occur by chance, and a nonrejection does not prove randomization.')
para('Offer/IV intervals remain asymptotic HC2/t or robust AR intervals; the permutation balance procedure does not convert them into exact randomized inference. Reported five-policy and four-schooling Holm families were chosen during revision. The combined-nine sensitivity retains private attendance and highest grade, not repetitions. Three lotteries are not enough for conventional cluster-asymptotic inference; assignment and dependence information still matters.')

slide(22,'Appendix 7: schooling effects by application age',['age_groups','age_effects','age_heterogeneity'],'1, 2, 11')
para('<b>Regression equation:</b> Within baseline-age group g: Y_i = alpha_g + tau_g Z_i + e_i. Joint test: all three tau_g are equal.')
para('<b>Visual:</b> the four complementary schooling outcomes by the same confirmed pretreatment-age bins as slide 8. Headers use the full-bin totals 215,634,271; each effect/interval/p uses its own outcome-observed sample. These are not grade cohorts, and there are no grade-conditioned or age-group IV estimates.')
rows=[]
for y in S:
    cells=[]
    for g in G:
        r=one('age_effects',y,age_group=g);cells.append(effect(r)+'; '+ci(r)+'; N='+r['n'])
    a=one('age_heterogeneity',y);rows.append([label(y)]+cells+[p(a['p_value']),p(a['holm_p'])])
table(['Outcome','Age 10-11','Age 12-13','Age 14-18','Joint p','Holm p'],rows,[128,102,102,102,47,47])
para('<b>Sample and model:</b> age_at_application determines bins before assignment. Within A2020/group, retain every observed Y, irrespective of later grade, school sector or work. Fit Y~selected with intercept; estimate mean differences and HC2/t(n_group-2) intervals/p. The 56 unknown baseline ages remain in the main pooled-age ITT but are unclassified here. No follow-up age is used to fill baseline age for grouping.')
para('<b>Equality test:</b> compare the three independent subgroup effects with the same two-restriction HC2 Wald/F procedure defined on slide 8: L contrasts the middle/oldest effect with the youngest, covariance L diag(SE squared) L\', df=(2,sum N_group-6). The final column on the slide reports the raw joint p, while the CSV also records a Holm adjustment across these four schooling tests.')
para('No schooling-outcome joint equality test rejects at 5%. Individual groups can have positive private-attendance effects with different p-values without establishing different treatment effects across ages. Timing, outcome levels and remaining measurement errors may also vary by age; interpret descriptive patterns cautiously.')
para('The binary outcomes enrolled/private use percentage points; highest grade and repetitions remain grade/count units. A younger/older applicant label is justified by baseline age; assigning the bins to grades 6/7/8 would add information absent from the data. The original grade-completion conflict flags remain unresolved and reported outcomes stay in these models.')

slide(23,'Appendix 8: offer effects with controls and fixed effects',['fe_itt','fe_category_counts'],'1, 2, 5, 12')
para("<b>Regression equation:</b> Y_i = alpha + tau Z_i + X_i'beta + SES-category effects + neighborhood-category effects + e_i. X contains male, imputed baseline age and its missingness flag; phone is constant.")
rows=[]
for y in P+S:
    r=one('fe_itt',y);rows.append([label(y),effect(r),ci(r),p(r['p_value']),p(r['holm_p']),r['n']])
table(['Outcome','Adjusted effect','95% CI','Raw p','Holm p','N'],rows,[161,81,120,55,57,54])
para('<b>Specification:</b> Y_i = alpha + tau Z_i + beta_m male_i + beta_a age_imp_i + beta_u age_missing_i + sum_s gamma_s 1(SES=s) + sum_j eta_j 1(neighborhood=j) + e_i. The requested phone term is included in the formula but omitted as aliased: has_phone=1 for every A2020 applicant, so its coefficient is not separately identified from the intercept.')
para('Impute missing baseline age using the full A2020 observed mean, <b>12.59375</b>, and retain its missingness indicator. SES and neighborhood are separate categorical fixed effects, with explicit Missing levels (186 SES, 279 neighborhood). They are not numeric scores or SES-by-neighborhood interactions. Reference categories are SES 1 and neighborhood 1; one category per factor is absorbed into the intercept. Only missing Y is excluded; do not drop applicants merely because these covariates are missing.')
para('<b>Interpretation:</b> tau is an additive adjusted offer contrast, not the raw mean selected minus control. There are no assignment-control interactions. This differs from slide 18\'s interacted numerical-SES adjustment. The main unadjusted A2020 analysis stays primary; adjustment is not evidence that any failure of randomization has been repaired.')
para('<b>Inference:</b> applicant HC2/t with rank 26 and df=n-26; no neighborhood clustering is introduced by including fixed effects. Sparse cells warrant caution: SES 4 has six applicants, SES 5 two, neighborhood 14 three. Maximum leverage is about .501; HC2 accounts for leverage but cannot ensure good finite-sample approximation. Raw p-values are displayed; separate five/four Holm values are above. Hours is -1.25, raw p=.046, policy-family Holm=.230.')
units_note()

slide(24,'Appendix 9: IV with controls and fixed effects',['fe_iv','fe_category_counts'],'1, 2, 5, 7, 8, 12')
para("<b>Regression equation:</b> Y_i = alpha_Y + rho Z_i + X_i'gamma_Y + SES effects + neighborhood effects + e_i; D_i uses the same design with coefficient pi on Z. beta_IV = rho/pi.")
rows=[]
for y in P:
    r=one('fe_iv',y);rows.append([label(y),effect(r),ar(r),p(r['ar_p_zero']),r['n'],v(r['first_stage_F'],1,1),p(r['first_stage_p'])])
table(['Outcome','IV effect','95% robust AR set','AR p','N','FS F','FS p'],rows,[150,65,134,49,44,43,43])
para('<b>Sample:</b> A2020 applicants with common observed Y,in_private_now,selected. Keep the full-cohort baseline age imputation and categorical Missing levels described for slide 23. Outcome/private missingness determines N=1,162 or 1,161; baseline-covariate missingness does not create extra exclusions. Phone remains constant and is removed by the rank check.')
para('<b>Instrument design:</b> W = [intercept,Z,male,age_imp,age_missing,SES indicators,neighborhood indicators]. Fit Y and D jointly on the identical W and rows, with additive category effects. The excluded instrument is Z; pretreatment controls appear in both equations. The controlled ratio rho_Z/pi_Z equals the just-identified covariate-adjusted 2SLS coefficient on D. This is distinct from the fewer-control IV sensitivity on slide 19.')
para('<b>Uncertainty:</b> form HC2 joint covariance for the two Z slopes using W leverage, then invert (rho-b pi) squared &lt;= t(.975,n-rank(W)) squared x [Vrr-2bVrp+b squared Vpp]. Rank is 26, so df=1,136 or1,135. Use robust AR sets rather than ordinary second-stage OLS SEs. First-stage F=(pi/SE_HC2(pi)) squared and FS p tests pi=0; AR p tests beta=0. They are not interchangeable.')
para('The hours coefficient is -7.58/week with AR set [-15.91,0.25] and raw AR p=.057; it is not statistically distinguishable from zero at 5%. The five IV Holm p-values in fe_iv.csv also do not reject. Binary effects and sets are percentage points, not relative percentages. Values use full precision before the slide rounding rules.')
para('SES/neighborhood adjustment does not establish exclusion, monotonicity, no interference or a valid current-school snapshot treatment. With heterogeneous effects, interpretation also depends on the adjusted IV\'s complier weighting. Rare category levels and leverage remain qualifications. These exploratory local effects are not generally the ATT among all actual private-school attendees. The pooled-age A2020 offer effects remain primary.')

def footer(canvas,doc):
    canvas.saveState();canvas.setStrokeColor(colors.HexColor('#D5DFE5'));canvas.line(42,35,570,35)
    canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#516573'))
    canvas.drawString(42,23,'DIL slide companion | A2020 primary | Review draft; nothing submitted')
    canvas.drawRightString(570,23,str(doc.page));canvas.restoreState()
doc=SimpleDocTemplate(str(OUT/'DIL_slide_companion.pdf'),pagesize=(612,792),leftMargin=42,rightMargin=42,topMargin=39,bottomMargin=46,title='How every slide is produced - DIL slide companion',author='AI-assisted analysis for applicant review')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
(OUT/'DIL_slide_companion.md').write_text('\n'.join(md),encoding='utf-8')
print(OUT/'DIL_slide_companion.pdf')
