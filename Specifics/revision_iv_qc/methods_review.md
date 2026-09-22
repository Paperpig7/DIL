# Independent policy-effect and IV review

This review recalculates estimates directly from the three raw CSV files without modifying the production analysis or any raw value. From the assessment folder, run `Rscript revision_iv_qc/check_iv.R`; an absolute script path also works from any directory. The CSVs and console output suppress asymptotic inference for constant outcomes. All results use applicant-level independent-observation robust variance approximations; the data do not provide enough assignment-unit information to validate a different clustering scheme.

## Primary target and model

Use municipality A's 2020 lottery-applicant cohort as the primary target. Other cohorts are separate contextual checks. Differences across cohorts cannot isolate duration effects because application year, possibly follow-up duration, and municipality can also differ. The study's approximate three-year statement and the observed age patterns should be described together; no survey year is observed.

The main policy effect is the lottery-offer intention-to-treat (ITT): the mean outcome of selected applicants minus the mean outcome of unselected applicants. It is relevant to offering the program under its observed take-up and renewal pattern. It is not automatically an effect for every resident of the municipality. Use every observed outcome regardless of whether private schooling is observed. For the five new policy outcomes, the A2020 unadjusted effects are:

| Outcome | ITT | 95% HC2/t interval | Nominal p | Five-outcome Holm p |
|---|---:|---:|---:|---:|
| Years in school since allocation | 0.0931 years | -0.0143 to 0.2004 | .0892 | .2677 |
| Married/cohabiting | -0.8841 percentage points | -2.1808 to 0.4127 | .1813 | .3626 |
| Has a child | -1.2644 percentage points | -3.2252 to 0.6965 | .2061 | .3626 |
| Working | -4.1334 percentage points | -8.4336 to 0.1668 | .0596 | .2382 |
| Hours worked per week | -1.4635 hours | -2.7643 to -0.1626 | .0275 | .1375 |

The overall private-school attendance first stage in A2020 is +15.91 percentage points, 95% CI 10.38 to 21.44; observed private attendance is 53.75% in controls and 69.66% among lottery winners. Its role is both a policy outcome and evidence that the proposed instrument shifts private attendance.

All five main policy effects are imprecise after Holm correction. Reduced work may be consistent with more time available for study, but a welfare improvement cannot be asserted without earnings, learning, costs and preferences. Years in school has chronology/definition flags in the data audit and should retain that caveat even though the user has prioritized it.

## Baseline comparison: final production calibration

The conditional-randomization Mahalanobis test holds full baseline controls and each cohort's offer count fixed. With 9,999 simulated allocations and seed 20260922, the production p values are A2020 .6038, A2022 .1162 and B2018 .0152. Independent reconstruction reproduces the statistics and simulated p values exactly. A2020 provides no evidence of joint imbalance; B2018 warrants extra caution. The very small A2022 reverse-regression HC2 Wald p value is unreliable because all five missing-baseline-age cases are controls, creating a sparse nearly perfectly predicted cell. Treat that Wald result as a diagnostic rather than the main balance assessment.

## Private-school IV calculations

Instrument: `selected`, the lottery offer. Endogenous schooling measure: `in_private_now`. Main model includes an intercept and estimates each cohort separately. Do not use `receiving_aid_now` as the instrument because it is realized follow-up aid use, not randomized assignment.

Each IV row uses exactly the same applicants in its reduced form, first stage and 2SLS estimate: observed Y, Z and D. The ratio is beta = ITT(Y)/ITT(D). Outcome-specific missingness means these reduced forms differ slightly from the main policy ITTs. The analysis must print both sample sizes and must not divide an all-observed-Y ITT by an all-observed-D first stage.

Variance comes from the joint robust covariance of the reduced-form and first-stage slopes; it retains their covariance. The production-compatible results use HC2 based on instrument-regression leverage and t reference degrees of freedom n-2. The independent script also verifies the HC1 ratio-delta variance against a direct structural 2SLS sandwich using Y-alpha-beta*D residuals for all 15 cohort/outcome models. An ordinary second-stage OLS standard error is incorrect.

The Anderson-Rubin confidence set inverts the HC2 robust t test of `Y-beta*D ~ selected`. It solves `(rf-beta*fs)^2 <= tcrit^2*(var_rf - 2*beta*cov_rf_fs + beta^2*var_fs)`, retaining bounded, disjoint and unbounded cases. This is an asymptotic heteroskedasticity-robust weak-instrument procedure, not an exact randomization test. Instrument strength does not validate exclusion or monotonicity.

| A2020 outcome | N | IV estimate | 95% robust AR set |
|---|---:|---:|---:|
| Years in school | 1162 | 0.497 years | -0.209 to 1.094 |
| Married/cohabiting | 1161 | -6.637 percentage points | -15.510 to 1.286 |
| Has a child | 1161 | -9.090 percentage points | -22.138 to 3.263 |
| Working | 1162 | -24.803 percentage points | -52.933 to 2.427 |
| Hours worked | 1162 | -8.977 hours/week | -17.600 to -0.875 |

A2020 same-sample first-stage F values are approximately 32.2–32.7; A2022 values approximately 8.0–8.5 and B2018 approximately 5.7. Report weak-IV-robust confidence sets in all cohorts; do not use a mechanical F>10 rule as a guarantee. The AR null-effect p value for hours is .03165 and its Holm p across the five A2020 IV outcomes is .15823.

A2022 has no observed marriage or parenthood events in either treatment arm. Their estimated reduced form is zero, but conventional robust SEs collapse to zero. Suppress confidence intervals and p values as uninformative/not reported for zero-event outcomes; do not represent them as certain zero population effects.

## Identification limits

For a causal private-school interpretation, the design needs randomized assignment, a nonzero first stage, exclusion, monotonicity and no interference. With different probabilities across cohorts, pooling also requires appropriate cohort adjustment, which the revised primary analysis avoids.

Exclusion is especially demanding for `in_private_now`: the subsidy can reduce family education expenses or encourage academic effort/renewal, and past private-school experience can affect cumulative schooling, work and family outcomes even if current private attendance is the same. Some outcomes may predate the current attendance measurement. The instrument therefore changes a bundle of financial support and schooling history rather than only a contemporaneous private-school indicator. The numerical IV estimate should be presented as exploratory and conditional on these extra assumptions. The lottery ITT remains the more direct policy estimand.

Monotonicity concerns two counterfactual schooling decisions at the same follow-up: D(1)>=D(0) for each applicant. Someone observed in private school at grade 6 and outside it at follow-up is an observed leaver, not an identified defier. Neither observed take-up patterns nor a positive average first stage establish that no defiers exist. Leaving, changes in school availability or differential academic progression can motivate discussion without permitting classification of individual counterfactual types.

Under the IV assumptions, the ratio estimates the local average treatment effect (LATE) for applicants whose schooling choice is changed by the lottery. It generally does not identify the average treatment effect on all privately schooled applicants or all subsidy recipients. Alternative exposure definitions (`started_g6_private`, `started_g7_private`) have different first stages and correspond to different complier groups; they are sensitivity analyses, not interchangeable versions of a single universal effect.

## ATT discussion

Clarify the treatment definition before using ATT. If treatment is the randomized offer, random assignment makes the effect among those offered the program equal to the offer ATE in expectation. That is the policy ITT being estimated.

For actual subsidy receipt S, the recipient ATT is E[Y(1)-Y(0) | S=1]. Recipients select into use and renewal, so comparing recipients with nonrecipients does not estimate this effect. `receiving_aid_now` is defined as ANY current education subsidy/scholarship, and program-specific receipt histories are absent. It is 56.25% among selected A2020 applicants versus 5.53% among controls, confirming it is not synonymous with assignment.

With genuine program-specific receipt, one-sided noncompliance S(0)=0, exclusion and other IV assumptions, offer-IV can identify a recipient effect that coincides with recipient ATT because all recipients are compliers. Those conditions cannot be established with the available any-aid follow-up variable. For private schooling there is clearly two-sided uptake: 53.75% of A2020 controls are currently privately enrolled. Thus its LATE does not generally equal ATT; the effects for always-takers are not identified. Additional verified receipt dates/history and clearly stated assumptions are needed for a defensible program-recipient ATT.

## Sensitivity checks calculated independently

`independent_iv_sensitivities.csv` contains all three schooling definitions, all three cohorts and all five outcomes, with and without additive baseline controls. Controls are sex, recorded phone, baseline age, socioeconomic stratum and nonconstant missingness indicators; missing age/stratum values use their full-cohort means. The full instrument-regression leverage is used for HC2; t degrees of freedom are n minus its rank. No post-lottery measures are controls.

For A2020 adjusted current-school IV, the hours estimate is -8.157, conventional t interval [-16.133,-0.181], but AR set [-17.083,0.025] includes zero. This is another reason to report the AR result and avoid overstating the finding. Grade-6 entry has a weaker first stage (about 5.98pp, F12.6), whereas grade-7 entry has about 16.8pp (F46.7); effect magnitudes vary with exposure definition and sample.

## Methodological sources

These are methodological sources only; no outside estimates of this program were consulted.

- Angrist, Imbens and Rubin, [Identification of Causal Effects Using Instrumental Variables](https://www.nber.org/papers/t0136), working paper and publication record; [published article](https://users.nber.org/~rdehejia/%21%40%24AEM/Topic%2004%20IV/readings/angrist_imbens_rubin_JASA_1996.pdf). The article formalizes the complier interpretation and its assumptions.
- Mikusheva, [Robust Confidence Sets in the Presence of Weak Instruments](https://economics.mit.edu/sites/default/files/publications/thirdsubmission.pdf). Inverting robust tests permits confidence sets that reflect weak identification, including unbounded sets.
- [Stata documentation discussion of weak-instrument-robust tests](https://www.stata.com/stata-news/news39-3/weak-instruments-wacky-confidence-intervals/), for interpretation of Anderson-Rubin confidence sets.
