# Optional independent verification

This directory contains an independent Python check of the main R analysis. It is optional: the primary analysis runs using base R alone, and **`results/tables/` contains the authoritative results** used in the report and presentation.

Both Python scripts resolve data paths relative to their own location. They read `data/raw/` and write only files in this directory. They never alter the main analysis, authoritative results, or raw data.

## Run from the package directory

Python 3, NumPy, and pandas are required for these optional checks. With those packages available:

```sh
python3 estimates_independent/independent_analysis.py
python3 estimates_independent/verify_root.py
```

Run the main R analysis first if its output tables need to be regenerated:

```sh
Rscript code/run_analysis.R
```

## Contents and interpretation

- `verify_root.py` reproduces 70 numerical comparisons against the authoritative R tables, covering the main and adjusted estimates, sex-specific effects and direct interactions, robust standard errors, exclusions, and missing-outcome bounds. It writes `root_numerical_verification.csv` and stops with an error if any comparison differs by more than 1e-9.
- `root_review.md` documents the statistical and numerical review of the authoritative pipeline.
- `independent_analysis.py` preserves the initial independent exploratory analysis and writes its supporting CSV files. Its primary point estimates and robust standard errors match the R analysis. Its legacy normal-reference p-values and confidence intervals differ slightly from the authoritative R t-reference intervals.
- The initial exploratory covariate-adjusted fixed-effects model is a separate sensitivity specification: it uses cohort-median imputation and a common treatment coefficient without assignment-interacted covariates. The final R adjustment instead uses cohort-mean imputation, cohort-specific treatment effects, and assignment-interacted baseline controls. `verify_root.py` checks that final model directly.
- `statistical_review.md` records the initial statistical interpretation. Numerical values in the final report and `results/tables/` take precedence over this earlier memo.

The broad initial diagnostic that excludes age increments outside 2–4 years is not a recommended cleaning rule and is not part of the authoritative sensitivity analysis. It can disproportionately select applicants from different cohorts and does not resolve the survey-timing discrepancy.
