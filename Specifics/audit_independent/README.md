# Optional independent audit

This directory contains a separate Python cross-check of the supplied data. It requires Python 3, NumPy and pandas. It is optional: the authoritative analysis and complete final issue ledger are produced by the base-R pipeline in `code/run_analysis.R`.

From the extracted project folder, run:

```sh
python audit_independent/audit.py
```

The script resolves the included `data/raw/` directory relative to its own location, so it can also be invoked from another working directory. Optional `--input-dir` and `--output-dir` arguments allow other paths. Source files are read only. This audit regenerates its own CSV and Markdown outputs alongside the script; it does not modify the main analysis outputs.

`audit_report.md` explains the checks and conservative recommendations. `record_level_issues.csv` lists each issue with applicant ID and original values. `all_applicants_with_audit_flags.csv` retains all source fields and audit flags. `audit_summary.json` records source hashes and validation results. The small parent-age derivative demonstrates cell-specific handling of impossible reported parent ages; it does not replace the main derived dataset.

This independent audit was completed before two final review screens were added to the main R pipeline: highest grade below 5 despite intended grade-6 entry (applicant 100538), and reported school years below `highest_grade - 5` under an assumed grade-5 entry baseline (18 applicants). The authoritative `data/derived/issue_ledger.csv` and main analysis data include these additional flags. They identify unresolved eligibility or counting-convention concerns and do not recode or delete the affected outcomes.

Counts can overlap, and screening flags do not establish which source report is wrong. Consult the main report for the final analysis choices and sensitivity estimates.
