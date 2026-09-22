# Independent statistical review

The unit of randomization is the applicant. Treat lottery selection as the randomized offer, not actual aid receipt. Never regress outcomes on current aid receipt as if it were randomized: renewal depends on promotion, and controls can use other aid. The intervention is private-school subsidy access bundled with its renewal conditions, so the data do not separate the effect of private schooling from the incentive attached to promotion.

## Estimand and inference

For each outcome, calculate selected-minus-nonselected means separately in the three municipality–application-year lottery cohorts. Aggregate these differences using fixed cohort shares in the entire baseline sample (A2020: 1176/1618; A2022: 277/1618; B2018: 165/1618). The estimate targets the average offer effect for this applicant sample, at the observed cohort-specific follow-up horizons. Actual lotteries have different offer probabilities; an unadjusted pooled comparison can confound cohort composition and treatment.

HC2 covariance from a saturated cohort-by-selection regression equals the within-cell sample-variance formula: sum over cohorts of w² times (s1²/n1 + s0²/n0). Report normal-approximation confidence intervals. Applicant-level robust uncertainty fits the stated individual lotteries. Clustering by only three cohorts is inappropriate. If allocation actually occurred by household or school, that would require more design information and different inference.

A regression with a common selection coefficient and cohort fixed effects is also reasonable, but its implicit weights are proportional to observed n times p times (1-p), rather than the baseline cohort shares. Here this numerical difference is very small. A covariate-adjusted FE check using baseline sex, age, phone and SES reduces the enrollment point estimate to +0.081 percentage points and the grade estimate to +0.103 grades, with private-school and repetition conclusions intact. This is a sensitivity check with a slightly different weighting model.

## Main findings

| Outcome | Cohort-weighted control mean | Offer effect | 95% CI | p | 4-outcome Holm p |
|---|---:|---:|---|---:|---:|
| Currently enrolled |84.17%|+1.73 pp|−1.73 to +5.19 pp|.327|.327|
| Currently private school |54.40%|+16.19 pp|+11.54 to +20.85 pp|<.001|<.001|
| Highest grade completed |7.339|+0.128|+0.040 to +0.216|.0046|.0137|
| Total grade repetitions |0.220|−0.055|−0.099 to −0.012|.0128|.0255|

The strongest evidence is increased private enrollment; grade progression improves modestly, while there is no clear evidence of increased overall enrollment. In levels, grade repetitions fall by roughly 25% of the standardized control mean, but avoid calling this a 5.5 percentage-point reduction: it is a count.

Female-versus-male patterns are exploratory. Female/male private effects are +19.03/+12.84 pp, but the direct interaction p=.194. Corresponding interaction p-values are .094 for enrollment, .260 for completed grade, and .545 for repetitions. A significant effect for one sex and insignificant effect for the other is not evidence that effects differ.

## Missingness and record issues

All 1618 baseline IDs have exactly one follow-up record. This rules out unmatched-person attrition in the supplied files, not every possible form of nonresponse. Outcome item missingness remains: enrollment 11; private attendance 18; highest grade 0; repetitions 8. Use outcome-specific samples and report denominators. Selected–nonselected missing-rate differences are small and not statistically distinguishable from zero; this does not prove missingness is ignorable.

Under extreme imputations of binary missing responses, the identified point-effect ranges are enrollment +1.15 to +2.48 pp, private attendance +15.02 to +17.22 pp. With repetitions bounded by the dictionary at 0–3, its range is −0.0768 to −0.0469. These intervals are missing-data identification bounds, not sampling-confidence intervals.

Age increments reveal a study-description/data discrepancy: A2020 predominantly +2/+3 years, A2022 predominantly +0/+1, and B2018 predominantly +4/+5. Do not impose baseline age +3 or label every departure as an error. Without interview year or birth dates, exact reconciliation is impossible. There are 11 negative increments, which are internally inconsistent and deserve record-level flags. Keep unrelated schooling outcomes and both raw ages; omit ages from primary outcome estimation. Excluding these 11 records scarcely changes primary estimates. An A2020-only result is a useful approximately-three-year cohort sensitivity, though it targets a different applicant population.

Fourteen unique students have a reported highest grade reaching a threshold but a contradictory completion indicator (14 for grade 6, 13 for grade 7, 13 for grade 8). Retain and flag raw source values, rather than declaring one source authoritative. Excluding those records gives a highest-grade effect +0.1259, close to +0.1279 originally. Flagging itself should not be confused with validated correction.

A diagnostic file includes exclusion of age increments outside 2–4, but this is intentionally broad and should not be a preferred cleaning rule. It disproportionately removes whole cohorts, selects using a follow-up measurement, and does not resolve the timing discrepancy.

Baseline diagnostics show selected applicants are 0.144 years younger among observed ages; their age missingness is 2.11 pp lower and phone availability 1.68 pp higher. Each nominal p is around .03. Sex and observed SES show no clear imbalance. These are chance-compatible diagnostics with multiple comparisons, not grounds for overruling documented randomization. Covariate adjustment is useful as a sensitivity; do not adjust for parental attributes or survey administration variables collected only at follow-up without establishing that they are pre-treatment and unaffected by selection.

The largest cohort (A2020, 72.7% of applicants) provides nearly all of the grade-progression signal: +0.188 grades (95%CI .079 to .296). A2022 and B2018 grade estimates are −.053 and +.006, with broad uncertainty. Do not treat common private-school effects across cohorts as proof of equal academic effects or a uniform 3-year endpoint.
