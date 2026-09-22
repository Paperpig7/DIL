# Private-school transitions: independent audit

This audit supports the requested revision with A2020 as the main cohort. Raw inputs are unchanged. Run `python3 transition_audit.py` from this directory, or give the script's full path from any directory. Only the Python standard library is required. All CSVs retain raw missing cells as blank.

## Main finding

Some selected applicants report earlier private attendance and no current private attendance. **This does not identify IV defiers.** A defier would attend privately without an offer and not attend privately with an offer at the same defined time. Only one of those potential choices is observed for each applicant. A change in attendance over time is a different comparison.

The assignment variable is `selected`, an offer in the lottery. There is no program-specific receipt or renewal history. `receiving_aid_now` records **any** education subsidy or scholarship in the survey year, so it cannot establish when this particular program's payments started or stopped.

`started_g6_private` is also a post-allocation outcome: the program begins when applicants enter grade 6. It is not private-school attendance measured before random assignment. Conditioning on G6-private attendance changes the composition of the selected and nonselected groups. The conditional exit rates below are descriptive, not causal effects of the subsidy on exiting.

## Private in grade 6, nonprivate at current follow-up

The denominator is applicants reporting `started_g6_private = 1` with `in_private_now` observed. An exit is `in_private_now = 0`. A missing current status remains unknown and is excluded from that denominator, not coded as an exit. Still-enrolled and not-enrolled columns subdivide the observed exits using `in_school_now`.

| Cohort | Lottery status | G6 private | Current status unknown | Observed denominator | Currently nonprivate | Percent | Still enrolled | Not currently enrolled |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| A2020 | Not selected | 503 | 5 | 498 | 208 | 41.77% | 127 | 81 |
| A2020 | Selected | 554 | 2 | 552 | 150 | 27.17% | 68 | 82 |
| A2022 | Not selected | 115 | 0 | 115 | 32 | 27.83% | 25 | 7 |
| A2022 | Selected | 127 | 1 | 126 | 11 | 8.73% | 8 | 3 |
| B2018 | Not selected | 38 | 0 | 38 | 13 | 34.21% | 9 | 4 |
| B2018 | Selected | 71 | 1 | 70 | 20 | 28.57% | 7 | 13 |

All 434 G6-to-current exits have observed current enrollment. An enrolled nonprivate student is consistent with a sector change. A student who is not currently enrolled could have withdrawn or completed schooling; the supplied fields do not identify the reason, so these are not automatically labelled dropouts. None of the 1,618 applicants reports current private attendance while reporting no current school enrollment.

Using private attendance at **either grade 6 or grade 7** as the starting criterion identifies 439 current exits, including 184 selected applicants: 151 in A2020, 12 in A2022 and 21 in B2018. These five additional exits began grade 6 nonprivately and grade 7 privately. The raw histories make the definition transparent; do not mix this count with the G6-only table above.

## Histories involving grade 7

Among A2020 applicants who started grade 6 privately, 60/554 selected and 125/503 nonselected report not starting grade 7 privately. These are not necessarily sector changes: `started_g7_private = 0` may also include applicants who did not reach grade 7. The data do not provide a separate not-yet-reached category or exact transition dates.

The reported pattern `1 -> 0 -> 1` for G6, G7 and current private attendance occurs for 23 applicants: A2020 has 7 selected and 4 nonselected; A2022 has 3 selected and 7 nonselected; B2018 has 0 selected and 2 nonselected. This can be consistent with leaving private school and returning, but these three fields alone do not establish the complete sequence or reason. The records should be retained with their raw history, not forced into a permanent-compliance category.

Examples, all selected A2020 applicants:

| ID | G6/G7/current private | Current enrollment | Any current aid | Interpretation and handling |
|---|---|---:|---:|---|
| 100031 | 1/1/0 | 1 | 0 | Earlier private attendance; currently enrolled nonprivately. Retain as observed exit. |
| 100036 | 1/0/0 | 0 | 0 | Earlier private attendance; not currently enrolled. Retain; reason unobserved. |
| 100062 | 1/0/1 | 1 | 0 | Nonmonotone reported attendance history. Retain; do not label an IV defier. |
| 100203 | 1/1/unknown | unknown | 0 | Current private status missing. Retain original record; current transition remains unknown. |
| 100449 | 1/1/unknown | 1 | 0 | Current enrollment does not resolve public/private status. Do not infer private status. |

The ID-level files contain **every** matching record and all original fields, not only these examples.

## Relevance and monotonicity

The independent observed-means first-stage checks are:

| Cohort | Offer effect on G6 private (pp) | Offer effect on G7 private (pp) | Offer effect on current private (pp) |
|---|---:|---:|---:|
| A2020 | +5.961 | +16.744 | +15.909 |
| A2022 | -2.161 | +16.481 | +15.995 |
| B2018 | +26.834 | +21.537 | +18.550 |

Each column uses available responses for that outcome. The authoritative regression pipeline should provide standard errors and first-stage statistics, including on each IV outcome's complete-case sample. A positive first stage supports relevance but does not establish no defiers. The negative A2022 G6 point estimate alone does not establish defiers either; sampling uncertainty must be considered, and the treatment definition must stay fixed.

Use the lottery offer as the instrument. Choosing current private attendance as the endogenous treatment does not turn these three histories into a complete measure of private-school exposure. The subsidy may affect earlier attendance, duration, school quality, household resources, or renewal incentives without changing the current private indicator. These possibilities matter for exclusion, particularly for cumulative years of schooling and family/work outcomes. Current exit histories reinforce the need to state the IV interpretation conditionally and separately from the causal offer effect.

## `years_in_school`: keep the supplied definition and explain uncertainty

The dictionary says "Number of school years completed since the allocation." Do not relabel it as lifetime schooling attainment or replace it with `highest_grade`. There are 8 missing responses.

| Cohort | Observed N | Mean reported years | Most common value (N) | Values above 4 years | Median reported age change |
|---|---:|---:|---|---:|---:|
| A2020 | 1171 | 3.655 | 4 (875) | 47 | 2 |
| A2022 | 275 | 2.062 | 2 (235) | 1 | 1 |
| B2018 | 164 | 5.201 | 6 (116) | 128 | 5 |

These distributions support treating the cohorts separately and are consistent with different exposure periods, but they do not verify exact follow-up dates. There is no interview year. The approximately three-year statement and school-year counting convention need clarification. Retain observed values with explicit timing flags; do not apply a uniform three-year cap or discard B2018 values above four years. Differences across cohorts can also reflect age, cohort composition, or place, not just elapsed time.

## Output inventory

- `all_records_with_history.csv`: 1,618 merged raw records and explicit transition classifications.
- `all_observed_private_exit_records.csv`: every observed G6-to-G7 nonprivate-start pattern or earlier-private-to-current nonprivate pattern, with all raw values.
- `selected_current_private_exit_records.csv`: all 184 selected applicants private in G6 or G7 and nonprivate currently.
- `g6_private_g7_nonprivate_current_private_records.csv`: all 23 reported 1/0/1 histories.
- `transition_counts_by_cohort_arm.csv`: numerators, denominators, unknown-status counts, and schooling-status subdivisions.
- `history_counts_by_cohort_arm.csv`: all observed three-state histories, including explicit unknowns.
- `history_missingness_by_cohort_arm.csv`: missingness and baseline denominators.
- `private_and_school_year_means_by_cohort_arm.csv`: outcome means and observed sample sizes.
- `school_year_counting_diagnostics.csv`: ID-level school-year, grade, repetition, age and timing review values.
- `audit_summary.json`: aggregate consistency checks.

No record is labelled a defier or deleted because it has a transition. No aid-history or private-attendance value is imputed. This audit is descriptive and does not estimate causal conditional exit effects.
