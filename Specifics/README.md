# DIL assessment draft

Start with the editable deck at `presentation/output/DIL_Assessment_Baseline.pptx` and its detailed slide-by-slide companion, `report/DIL_slide_companion.pdf` (also available as editable Markdown). The deck has 15 main slides and 9 appendix slides.

**To reproduce the results shown in the slides, use `code/slide_regressions.md`.** Its 14 explained code chunks contain the same 316 lines as `code/slide_regressions.R`. This independent base-R script reads the original baseline/follow-up CSVs and produces exactly the displayed specifications and supporting descriptive counts. It includes offer effects, first stages, IV results, sensitivity checks, sex contrasts, application-age groups, controlled models with fixed effects, data checks and balance p-values. The main offer tables show both control and treatment group means; “treatment group” means lottery-selected applicants.

**Current analysis:** A2020 applicants pooled across application ages remain primary. All five policy outcomes and four schooling outcomes are retained. Ages 10–11, 12–13 and 14–18 form an additional exploratory breakdown; they are application-age groups, not verified grades. Controls use baseline sex, phone, age and age missingness, plus separate categorical SES and neighborhood fixed effects. Missing SES and neighborhood have explicit categories. Phone is constant in A2020 and cannot have a separately estimated coefficient. The controlled offer and IV models are sensitivity checks. A2022 and B2018 remain separate cohort checks. Dedicated main slides discuss the comparison group as a counterfactual and schooling effects for girls and boys. Each regression table has its model equation above it. Observed private-school exits and IV limitations remain covered. ATT now concerns private-school attenders, with lottery selection as the offer; two-sided uptake means the IV complier effect is not generally all-attender ATT.

The current deck and companion report use the 17 CSVs in **`results/slide_regressions/`**. The earlier comprehensive report, `report/DIL_analysis_report.pdf`, supplies additional audit detail and the previous analysis scope; it does not contain the latest age groups, fixed-effects models or revised private-school ATT framing. Its full pipeline is explained in `code/run_analysis.md`, whose 41 annotated blocks preserve every line of `run_analysis.R`. The `results/tables/revised_*` outputs document that prior A2020 revision. Unprefixed model tables such as `primary_effects.csv` preserve the earlier analysis pooling different cohorts, which is supplementary and distinct from pooling ages within A2020.

This is a review draft. Nothing has been uploaded or submitted. The final AI chat PDF and public chat link are not yet included. Add them after completing your revisions, as required by the assessment. The AI-use note is not a substitute for those items.

## Reproduce the analysis

Requires **R**, with no additional R packages. Tested with R 4.3.3.

From the extracted package folder:

```sh
Rscript code/run_analysis.R
```

Or run the script by its full path from any folder. Paths resolve relative to the script. No personal paths or edits are required. This command regenerates the full analysis tables, charts, audit ledgers and derived analysis datasets under `results/tables/`, `results/figures/` and `data/derived/`. Raw files remain unchanged.

For all results displayed in the current slides, run:

```sh
Rscript code/slide_regressions.R
```

This independently regenerates 17 CSVs under `results/slide_regressions/`, with no existing derived datasets or full-analysis result tables required. The annotated Markdown maps every output to the slide using it. Ordinary offer/sensitivity p-values use HC2/t tests; direct age-group equality tests use HC2/F tests. IV p-values are explicitly labeled AR tests to match the displayed confidence sets. Zero-event outcomes in A2022 and the youngest A2020 group retain missing inferential p-values. The five policy and four schooling testing families are stated separately.

The 56 A2020 applicants with missing application age remain in the main and controlled analyses but cannot enter the age-group tables. Missing outcomes are omitted separately by outcome. The fixed-effects models retain missing baseline categories, impute baseline age with its full-cohort mean plus an indicator, and use applicant-level HC2 standard errors; fixed effects do not mean clustered standard errors. No follow-up variables are controls.

The current offer-effect analysis uses within-cohort mean differences, applicant-level HC2 standard errors, t-reference intervals and Holm corrections separately for five policy outcomes and four schooling outcomes. A combined nine-test correction is also saved. It includes a fixed-count randomization balance check (9,999 draws), missingness, A2020 sex interactions, baseline adjustment, HC3 checks, targeted record exclusions and logical binary-outcome missingness bounds.

IV uses lottery selection as the instrument and private-school attendance as the exposure. Each outcome's reduced form and first stage use the same complete sample. The script retains their joint HC2 covariance and reports conventional ratio intervals plus approximate robust AR-type confidence sets, including unbounded or disjoint sets where appropriate. Current attendance is the main IV definition; G6/G7 entry and additive baseline adjustment are sensitivities. These estimates require stronger identification assumptions than the policy ITT. No observed school exit is labeled an identified defier. With private attendance defined as treatment uptake, IV targets offer-induced attenders under its assumptions. The all-private-attender ATT requires additional assumptions because control applicants also attend private school; no separate ATT number is claimed.

## Contents

- `data/raw/`: exact supplied CSVs, including the original dictionary.
- `data/derived/analysis_data.csv`: every applicant, original fields, explicitly named clean derivatives and audit flags.
- `data/derived/adjusted_analysis_data.csv`: also includes all imputed and centered baseline covariates used in adjustment.
- `data/derived/issue_ledger.csv`: ID-level issues, original values, rules and actions.
- `data/derived/age_review_records.csv`: all 419 missing or off-window age pairs.
- `data/derived/age_decreased_records.csv`: the 11 declining-age cases.
- `data/derived/schooling_conflict_records.csv`: the 14 grade-completion conflicts.
- `data/derived/private_school_transitions.csv`: all applicants' reported G6/G7/current private-school histories, with missing statuses preserved.
- `data/derived/private_school_exit_records.csv`: exact IDs and original values for current nonprivate attendance after reported G6 or G7 private attendance, selected and nonselected.
- `results/tables/`: broader full-analysis numerical results and diagnostics; the latest slide-specific additions are under `results/slide_regressions/`.
- `results/slide_regressions/`: the current deck’s numerical evidence and supporting counts, generated independently by the focused script.
- `results/figures/`: analysis graphics as PDF and PNG.
- `report/`: the current slide-by-slide companion in PDF/Markdown, plus the earlier comprehensive audit report.
- `presentation/output/`: editable PowerPoint with 15 main slides and 9 appendix slides, including speaker notes.
- `documentation/`: provenance, hashes, variable definitions and AI-use disclosure.
- `audit_independent/`, `estimates_independent/`: optional independent crosschecks. These use Python with numpy and pandas. Their normal-reference intervals can differ slightly from the authoritative R t-reference intervals.
- `revision_iv_qc/`, `revision_transitions_qc/`: independent checks of revised ITT/IV estimates, school histories and exact record IDs. Their methods notes identify the authoritative matching HC2/t calculations. The independent transition audit uses Python's standard library; IV verification uses base R.

## Edit the report or slides

The slides are ordinary editable PowerPoint objects. The Markdown report can be edited directly. To regenerate the current companion report from the focused result tables, the optional authoring script uses Python 3 and ReportLab:

```sh
python -m pip install reportlab
python code/build_slide_report.py
```

Use `code/build_report.py` for the earlier comprehensive report. The report builders regenerate their Markdown too, so preserve any manual Markdown revisions before running it. Narrative text is editorial: if the raw data, cleaning or models change, review all narrative statements and revise the slide deck accordingly. The core analysis command does not automatically update the prose or PowerPoint.

## Before eventual submission

Review the assumptions, the timing discrepancy and flagged records. Add the final chat PDF and public link. Rename the final compressed folder to the exact FirstName_LastName.zip format requested by Canvas. This draft zip has intentionally not been uploaded or submitted.
