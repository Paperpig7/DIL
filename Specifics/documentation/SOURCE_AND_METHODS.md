# Sources and methods

## Assessment source

The Canvas assessment was read in Chrome on September 22, 2026:

https://canvas.uchicago.edu/courses/73831/quizzes/167188/take

The page describes a government education subsidy for low-income students entering grade 6 in private secondary school, renewable with academic progress. Oversubscribed municipalities allocate offers by lottery. Cohorts are A2020, A2022 and B2018, with different selection probabilities. The page describes follow-up approximately three years after application. The data's age increments conflict with a uniform horizon, which the analysis discloses.

The requested analysis asks whether the comparison group is credible, estimates the main schooling effects and asks whether effects differ between girls and boys. It calls for explanation of regression specification, unit, controls, data structure, standard errors and tests. Secondary household/work outcomes are optional. The deliverables include a slide deck with a table and visualization plus reproducible code and derived data. AI assistance is allowed, with final chat PDF and link required.

The applicant subsequently requested that A2020 become the primary cohort, based on clarification they reported receiving by email. Those emails were not independently read or verified. The requested revision promotes five broader policy outcomes (school years since allocation, marriage/cohabitation, parenthood, employment and hours), retains schooling outcomes, and adds observed exits, ATT discussion and schooling IV analysis. These are transparent draft revisions, not prospectively registered analysis choices. A2022 and B2018 are separate checks, with no claim that their differences isolate duration effects.

## Raw files

The included CSVs are copies of the assessment files downloaded on September 22, 2026 at approximately 12:17-12:18 local time. They were read without modification. `raw_sha256.csv` records hashes and file sizes. All study effect estimates are calculations from these files.

The source dictionary uses `interview_month`, but the actual follow-up file uses `survey_month`. The analysis keeps the observed field name and assumes it describes the same interview-month concept. This alias needs confirmation from the provider. No interview year or exact interview date is inferred.

## Methodological references

- HC2 and stratified design-based variance: [DeclareDesign estimatr mathematical notes](https://declaredesign.org/r/estimatr/articles/mathematical-notes.html).
- Assignment-interacted baseline adjustment: [Winston Lin, Agnostic notes on regression adjustments to experimental data](https://arxiv.org/abs/1208.2301).
- Holm multiple-testing correction: [R p.adjust documentation](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/p.adjust.html).
- Private-school ATT versus LATE, including always-attenders/compliers and one-sided uptake: [Angrist, Imbens and Rubin (1996), article and Rejoinder, pp. 469–470](https://www.math.mcgill.ca/dstephens/AngristIV1996-JASA-Combined.pdf).
- IV compliance types, exclusion, monotonicity and LATE: [Angrist, Imbens and Rubin (1996), Identification of Causal Effects Using Instrumental Variables](https://www.tandfonline.com/doi/abs/10.1080/01621459.1996.10476902).
- IV interpretation and assumptions: [Imbens (2014), Instrumental Variables: An Econometrician's Perspective](https://www.nber.org/papers/w19983.pdf).
- Confidence sets robust to weak instruments, including unbounded and disjoint sets: [Stata's weak-instrument inference documentation](https://www.stata.com/new-in-stata/inference-robust-to-weak-instruments/). The implementation here is a base-R inversion of an HC2 reduced-form t test, not a claim to reproduce every software default or exact finite-sample coverage.

These references support methods, not the study's empirical findings. The analytical implementation uses base R. Outcome and IV tests use robust t/F approximations. The separate joint-balance diagnostic reassigns labels with cohort-specific arm counts fixed and estimates a conditional randomization p-value with 9,999 draws; it is a Monte Carlo calculation, not exhaustive enumeration.

## Main analysis choices

- Target the offer effect for A2020 lottery applicants. This is not automatically an effect for all residents or all low-income children.
- Estimate A2022 and B2018 separately. Retain the earlier baseline-cohort-share pooled estimates only as supplementary calculations.
- Keep every baseline applicant and original value. Use observed responses separately by outcome.
- Use unadjusted within-cohort means for primary offer estimates and assignment-interacted baseline controls for sensitivity.
- Preserve unresolved primary outcome reports and provide targeted exclusion checks rather than guessed corrections.
- Avoid controlling for post-assignment household, administrative, receipt or school-choice variables.
- Present direct A2020 sex-interaction tests, correcting five policy interactions and four schooling interactions separately.
- Treat chronology and school-year plausibility screens as review flags, distinguishing them from verified domain violations.
- Use the lottery offer as Z and private attendance as D for exploratory IV. Fit both reduced forms on an identical sample, retain their joint covariance, and show approximate robust AR-type sets. Additive baseline adjustment and G6/G7 entry definitions are sensitivities.
- Define private-school attendance as treatment uptake and lottery selection as the subsidy offer. Distinguish ATT among private attenders from the IV effect among attendance compliers. Because controls also attend private school, one-sided uptake fails; identifying all-attender ATT requires additional assumptions about always-attender effects. Current aid receipt does not replace randomized assignment.
- Describe observed exits without calling them identified defiers. Monotonicity concerns two potential school choices for the same applicant at the same horizon, not change over time.
- Show multiple-testing families explicitly, including a combined nine-outcome sensitivity. These choices were revised after reviewing the draft and should not be described as preregistered.

## Application-age and fixed-effects revision

At the applicant’s request, the presentation adds groups defined only by age at application: 10–11 (215 applicants), 12–13 (634) and 14–18 (271). These bins were explicitly selected by the applicant after draft review. Missing baseline age (56 applicants) prevents grouping but does not exclude anyone from the pooled-across-ages primary A2020 analysis. These are not observed grade categories: the supplied data have no baseline-grade variable, and follow-up grade can respond to the offer. All program applicants target entry to grade 6.

Each age-group offer estimate uses its outcome-observed sample and applicant-level HC2/t inference. Equality of all three effects is tested directly with a two-restriction HC2/F test equivalent to a saturated age-by-assignment interaction. Holm corrections apply separately to five policy and four schooling equality tests. Group-specific p-values remain exploratory and unadjusted. Zero observed marriage/parenthood events in the youngest group prevent ordinary robust inference for those group effects and corresponding equality tests. No age-specific IV models are fitted.

Additional pooled A2020 regressions control for baseline sex, phone, age (full-cohort mean imputation plus missingness indicator), separate categorical SES fixed effects and separate categorical neighborhood fixed effects. Missing SES and neighborhood each enter an explicit missing category; these are not joint SES-by-neighborhood effects. Every applicant has a phone recorded, so that regressor is aliased with the intercept. The fitted design has rank 26. Standard errors remain applicant-level HC2, not neighborhood-clustered. No post-assignment variable is a control. These models differ from the retained earlier assignment-interacted specification using numeric mean-imputed SES.

The five controlled IV models use the same baseline covariates and fixed effects in both first stage and reduced form, with exact common outcome/private-status samples and joint-HC2 AR inference. Including controls does not validate exclusion or monotonicity. These additional analyses were requested after viewing earlier results and should not be described as prospectively registered.

The current deck and slide companion report are reproduced by `code/slide_regressions.R` / `.md`. The older full pipeline preserves broader audit and supplementary outputs. All raw files are unchanged.

## Equations, comparison credibility and revised ATT

The latest deck adds a dedicated counterfactual discussion and a main slide about girls/boys schooling effects, while retaining every earlier estimate. Equations above the regression tables specify the unadjusted offer model, subgroup interactions, additive or interacted covariate adjustment, and IV stages appropriate to each table. The sex discussion uses direct boys-minus-girls interaction tests across four schooling outcomes and their Holm correction, not comparisons of separate subgroup significance.

The A2020 lottery design and conditional baseline-balance p = 0.6038 support the control group as a credible counterfactual for the offer effect under the stated assignment, response and interference assumptions. Balance nonrejection does not prove implementation. Complete extract matching does not establish coverage of the original lottery roster. Policy outcomes have five or seven missing responses; current private attendance is missing for 10 of 583 controls and 3 of 593 selected applicants. Control private attendance is compatible with a valid offer comparison, while creating two-sided treatment uptake for private-school IV.

Following the applicant's clarification, let Z denote the subsidy offer (`selected`) and D private schooling (`in_private_now`). ATT_D = E[Y(1)-Y(0) | D=1], where outcomes are indexed by private schooling. Under the maintained IV assumptions, the lottery identifies the LATE among applicants with D(1)>D(0). Controls attend private school at about 53.8%, compared with 69.7% of selected applicants. Thus one-sided uptake D(0)=0 does not hold. Observed private attenders include always-attenders and compliers; the always-attenders' schooling treatment effects are not identified by assignment. LATE would equal all-attender ATT under an additional equality-of-mean-effects assumption across these types (constant effects is sufficient), or under one-sided uptake plus the remaining IV conditions, which the current uptake data contradict. These are assumptions, not empirical ATT estimates.

The focused script now generates 17 CSVs, omitting the obsolete current-aid means. The full earlier audit report retains its original subsidy-receipt discussion as historical material; the current slide companion is authoritative for the revised treatment definition.
