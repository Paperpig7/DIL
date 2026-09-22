"""Independent data-quality audit. Never overwrites source data.

Run from the project folder: python audit_independent/audit.py
Optional overrides: --input-dir /path/to/raw --output-dir /path/to/audit
Requires pandas and numpy. The audit flags uncertainty; it does not infer which
of two contradictory reports is true, and does not delete applicants.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import pandas as pd


def main():
    audit_dir = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-dir', type=Path, default=audit_dir.parent / 'data' / 'raw')
    parser.add_argument('--output-dir', type=Path, default=audit_dir)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    source_files = ['study_baseline.csv', 'study_followup.csv', 'data_dictionary.csv']
    checksums = {name: hashlib.sha256((args.input_dir / name).read_bytes()).hexdigest() for name in source_files}
    b = pd.read_csv(args.input_dir / source_files[0])
    f = pd.read_csv(args.input_dir / source_files[1])
    dictionary = pd.read_csv(args.input_dir / source_files[2])
    integrity = {}
    schema = {}
    inventories = []
    for name, frame in zip(source_files[:2], [b, f]):
        raw = pd.read_csv(args.input_dir / name, dtype=str, keep_default_na=False)
        integrity[name] = {
            'rows': len(frame), 'columns': len(frame.columns),
            'missing_ids': int(frame.applicant_id.isna().sum()),
            'duplicate_ids': int(frame.applicant_id.duplicated().sum()),
            'duplicate_rows': int(frame.duplicated().sum()),
        }
        expected = set(dictionary.loc[dictionary.File.eq(name), 'Variable'])
        schema[name] = {'dictionary_only': sorted(expected - set(frame)), 'data_only': sorted(set(frame) - expected)}
        for c in frame:
            numeric = pd.to_numeric(raw[c], errors='coerce')
            nonnumeric = raw.loc[numeric.isna() & raw[c].ne(''), c].value_counts().to_dict()
            inventories.append({
                'file': name, 'variable': c, 'parsed_type': str(frame[c].dtype),
                'n': len(frame), 'observed': int(frame[c].notna().sum()),
                'missing': int(frame[c].isna().sum()),
                'blank_strings': int(raw[c].eq('').sum()),
                'nonblank_nonnumeric_tokens': json.dumps(nonnumeric),
                'unique_observed': int(frame[c].nunique()),
                'minimum': numeric.min(), 'maximum': numeric.max(),
                'fractional_numeric_count': int((numeric.notna() & (numeric % 1).ne(0)).sum()),
                'negative_numeric_count': int(numeric.lt(0).sum()),
                'sentinel_candidate_count': int(numeric.isin([-999, -99, -9, -1, 99, 999, 9999]).sum()),
            })
    # validate rejects duplicate keys; outer join makes any unmatched records visible.
    d = b.merge(f, on='applicant_id', how='outer', validate='one_to_one', indicator=True).sort_values('applicant_id')
    integrity['merge'] = {str(k): int(v) for k,v in d._merge.value_counts().items()}
    d = d.drop(columns='_merge')
    d['cohort'] = d.municipality + '_' + d.application_year.astype(str)
    d['age_gap'] = d.age_at_survey - d.age_at_application
    # This is only a diagnostic sum, NOT a recovered date or an asserted survey year.
    d['application_year_plus_age_gap'] = d.application_year + d.age_gap
    d['mother_child_age_gap'] = d.mother_age - d.age_at_survey
    d['father_child_age_gap'] = d.father_age - d.age_at_survey
    issue_rows = []
    issue_summary = []

    def flag(name, mask, cols, explanation, recommendation, certainty='review'):
        mask = pd.Series(mask, index=d.index).fillna(False).astype(bool)
        d['flag_' + name] = mask.astype(int)
        issue_summary.append({'issue': name, 'n': int(mask.sum()), 'certainty': certainty,
                              'explanation': explanation, 'recommended_treatment': recommendation})
        for _, row in d.loc[mask].iterrows():
            values = {c: (None if pd.isna(row[c]) else (row[c].item() if isinstance(row[c], np.generic) else row[c])) for c in cols}
            issue_rows.append({'applicant_id': int(row.applicant_id), 'cohort': row.cohort,
                               'selected': int(row.selected), 'issue': name, 'certainty': certainty,
                               'observed_values': json.dumps(values), 'recommended_treatment': recommendation})

    flag('age_pair_missing', d.age_gap.isna(), ['age_at_application','age_at_survey'],
         'At least one age needed to assess change is missing.',
         'Do not fill ages using other-wave age minus three; retain applicant and other outcomes.', 'missing')
    flag('age_decreases', d.age_gap.lt(0), ['age_at_application','age_at_survey','age_gap'],
         'Follow-up age is lower than baseline age; both reports cannot be chronologically correct.',
         'Preserve raw values; flag both reports as unresolved; keep unrelated outcomes; sensitivity may omit these applicants.', 'contradiction')
    flag('age_unchanged', d.age_gap.eq(0), ['age_at_application','age_at_survey','age_gap'],
         'Age unchanged despite described approximately three-year follow-up.',
         'Flag timing discrepancy, not a proven typo; retain records and avoid adjusting for follow-up age.')
    flag('age_gap_outside_2_4', d.age_gap.notna() & ~d.age_gap.between(2,4), ['age_at_application','age_at_survey','age_gap'],
         'Age change outside a deliberately broad diagnostic interval around three years; exact dates unavailable.',
         'Keep in main sample; show cohort distribution and sensitivity; do not force every age gap to three.')
    grade_masks = []
    for g in (6,7,8):
        c = 'finished_g' + str(g)
        mask = d[c].notna() & d.highest_grade.notna() & d[c].ne(d.highest_grade.ge(g).astype(int))
        grade_masks.append(mask)
        flag('grade_' + str(g) + '_contradiction', mask, ['highest_grade','finished_g6','finished_g7','finished_g8','years_in_school'],
             'Highest grade completed conflicts with completion indicator for grade ' + str(g) + '.',
             'Source of error cannot be identified. Preserve reported outcomes; use separate sensitivity excluding contradictory grade records.', 'contradiction')
    flag('any_grade_contradiction', np.logical_or.reduce(grade_masks), ['highest_grade','finished_g6','finished_g7','finished_g8'],
         'At least one grade completion indicator disagrees with highest grade.',
         'No automatic overwrite of one measurement with another; analyze grade robustness on records without contradictions.', 'contradiction')
    for parent in ('mother','father'):
        gap = d[parent + '_child_age_gap']
        flag(parent + '_not_older_than_child', gap.le(0), [parent+'_age','age_at_survey',parent+'_child_age_gap'],
             'Reported parent age is no greater than applicant age.',
             'Set this parent-age cell to missing only in an explicitly cleaned derivative; retain applicant and other fields.', 'contradiction')
        flag(parent + '_age_gap_under_12', gap.gt(0) & gap.lt(12), [parent+'_age','age_at_survey',parent+'_child_age_gap'],
             'Reported parent-child age gap is positive but below 12 years.',
             'Flag as implausible for review; do not assume exact correction or remove applicant.')
        flag(parent + '_age_gap_over_60', gap.gt(60), [parent+'_age','age_at_survey',parent+'_child_age_gap'],
             'Reported parent-child age gap is greater than 60 years; unusual value, not necessarily impossible.',
             'Flag for review; preserve without an externally supported correction.')
    flag('nonworker_positive_hours', d.working.eq(0) & d.hours_worked.gt(0), ['working','hours_worked'],
         'No current paid work is reported together with positive hours worked per week.',
         'Retain raw reports; treat as unresolved definition/reporting conflict; check secondary work results excluding this record.', 'contradiction')
    flag('worker_zero_hours', d.working.eq(1) & d.hours_worked.eq(0), ['working','hours_worked'],
         'Paid work is reported with zero weekly hours; this can occur with temporary absence or distinct reference periods.',
         'Retain valid zero; flag for clarification. Do not replace zero hours with missing solely on this basis.')
    flag('years_in_school_above_4', d.years_in_school.gt(4), ['years_in_school','highest_grade','total_repeats','age_gap'],
         'Five or six completed school years since allocation appear long for a described approximately three-year follow-up.',
         'Retain and flag timing/definition ambiguity; do not use as a primary attainment outcome without clarification.')

    # Mechanical range and internal-consistency checks, including zero-count checks.
    binary = dictionary.loc[dictionary.Type.eq('0/1'), 'Variable'].unique()
    for c in binary:
        flag(c + '_invalid_binary', d[c].notna() & ~d[c].isin([0,1]), [c],
             'Observed value outside documented binary coding.', 'Set invalid cell to missing in a named clean derivative.', 'range')
    for c, lo, hi in [('ses_stratum',1,6),('neighborhood',1,19),('survey_month',1,12),('repeats_g6',0,3),('total_repeats',0,3)]:
        flag(c + '_out_of_range', d[c].notna() & ~d[c].between(lo,hi), [c],
             'Observed value outside dictionary limits.', 'Set invalid cell to missing in a named clean derivative.', 'range')
    for name, mask, cols in [
        ('private_but_not_enrolled',d.in_private_now.eq(1)&d.in_school_now.eq(0),['in_private_now','in_school_now']),
        ('g7_without_g6',d.finished_g7.gt(d.finished_g6),['finished_g6','finished_g7']),
        ('g8_without_g7',d.finished_g8.gt(d.finished_g7),['finished_g7','finished_g8']),
        ('g6_repeats_exceed_total',d.repeats_g6.gt(d.total_repeats),['repeats_g6','total_repeats']),
        ('any_repeat_disagrees_total',d.ever_repeated.notna()&d.total_repeats.notna()&d.ever_repeated.ne(d.total_repeats.gt(0).astype(int)),['ever_repeated','total_repeats']),
        ('hours_outside_0_168',d.hours_worked.notna()&~d.hours_worked.between(0,168),['hours_worked']),
    ]:
        flag(name,mask,cols,'Logical or physical constraint violated.','Preserve raw data; investigate and document outcome-specific treatment.','contradiction')

    pd.DataFrame(inventories).to_csv(args.output_dir/'variable_inventory.csv',index=False)
    pd.DataFrame(issue_summary).to_csv(args.output_dir/'issue_summary.csv',index=False)
    pd.DataFrame(issue_rows).to_csv(args.output_dir/'record_level_issues.csv',index=False)
    d.to_csv(args.output_dir/'all_applicants_with_audit_flags.csv',index=False)
    d.loc[d.age_gap.notna(), ['applicant_id','cohort','selected','age_at_application','age_at_survey','age_gap','application_year_plus_age_gap']].to_csv(args.output_dir/'age_comparison_all_observed.csv',index=False)
    pd.crosstab(d.cohort,d.age_gap,dropna=False).to_csv(args.output_dir/'age_gap_by_cohort.csv')
    cohort = d.groupby('cohort').agg(n=('applicant_id','size'),selected=('selected','sum'),age_pair_observed=('age_gap','count'),age_gap_mean=('age_gap','mean'),age_gap_median=('age_gap','median'),age_gap_min=('age_gap','min'),age_gap_max=('age_gap','max'),neighborhood_observed=('neighborhood','count'))
    cohort.to_csv(args.output_dir/'cohort_audit.csv')
    missing = []
    for c in list(b.columns) + [c for c in f if c!='applicant_id']:
        for keys, frame in d.groupby(['cohort','selected']):
            missing.append({'variable':c,'cohort':keys[0],'selected':int(keys[1]),'N':len(frame),'missing':int(frame[c].isna().sum()),'missing_pct':100*frame[c].isna().mean()})
    pd.DataFrame(missing).to_csv(args.output_dir/'missingness_by_cohort_arm.csv',index=False)
    # An optional derivative resolves only parent-age impossibilities. It is not
    # used to justify recoding the ambiguous age/grade/work variables.
    parent_clean = d[['applicant_id','mother_age','father_age']].copy()
    for parent in ('mother','father'):
        parent_clean[parent+'_age_clean'] = d[parent+'_age'].mask(d[parent+'_child_age_gap'].le(0))
    parent_clean.to_csv(args.output_dir/'parent_age_clean_derivative.csv',index=False)
    info = {'source_sha256':checksums,'integrity':integrity,'schema_mismatches':schema,
            'total_applicants':len(d), 'diagnostic_common_2022_or_2023_sum':int(d.application_year_plus_age_gap.isin([2022,2023]).sum()),
            'age_pairs_observed':int(d.age_gap.notna().sum()),
            'nonzero_issues':[r for r in issue_summary if r['n']]}
    (args.output_dir/'audit_summary.json').write_text(json.dumps(info,indent=2))
    report = make_report(d, info, pd.DataFrame(issue_summary), cohort)
    (args.output_dir/'audit_report.md').write_text(report)
    print(json.dumps({'integrity':integrity,'schema_mismatches':schema,'nonzero_issue_counts':{r['issue']:r['n'] for r in issue_summary if r['n']}},indent=2))


def make_report(d, info, issues, cohort):
    ages = d.loc[d.flag_age_decreases.eq(1),['applicant_id','cohort','selected','age_at_application','age_at_survey','age_gap']]
    grades = d.loc[d.flag_any_grade_contradiction.eq(1),['applicant_id','cohort','selected','highest_grade','finished_g6','finished_g7','finished_g8']]
    parents = d.loc[d.flag_mother_not_older_than_child.eq(1)|d.flag_father_not_older_than_child.eq(1),['applicant_id','age_at_survey','mother_age','father_age']]
    def table(frame):
        # Markdown without optional tabulate dependency.
        cells = [list(frame.columns)] + [[str(v) for v in row] for row in frame.itertuples(index=False,name=None)]
        return '\n'.join(['| '+' | '.join(cells[0])+' |','| '+' | '.join(['---']*len(cells[0]))+' |']+['| '+' | '.join(r)+' |' for r in cells[1:]])
    return f'''# Independent data-quality audit

## Scope and method

Read the two supplied CSVs and dictionary without modifying them. Inspected raw strings before numeric parsing, blank tokens, inferred types, numeric minima/maxima, fractional values, negative values and common sentinel candidates. Tested unique/nonmissing join keys, duplicate rows, outer-merge coverage, dictionary ranges, cohort/arm missingness and cross-field consistency. Saved every issue with applicant ID, original values and proposed handling in `record_level_issues.csv`; retained all applicants and raw fields in `all_applicants_with_audit_flags.csv`.

Both survey files contain 1,618 unique applicants with no duplicate or missing IDs, no duplicate rows, and complete one-to-one matching. The data have blank-cell missingness; no nonblank numeric missing-value tokens or common sentinel candidates were found. Documented binary and bounded categorical variables are within range. No ID-based evidence of respondent attrition appears in the supplied extracts; item missingness remains. This does not establish that the extracts include all applicants in the original administrative population.

The dictionary calls the follow-up month `interview_month`, whereas the data call it `survey_month`. The actual column contains integers 1–12; use the actual column name and record the dictionary discrepancy. Neither survey year nor exact interview/application dates are supplied.

## Ages: substantive timing discrepancy

Baseline age is missing for 64 applicants and survey age for 6 (one overlap), leaving 1,549 comparable pairs and 69 unassessable pairs. Of observed pairs, 350 (22.6%) differ by an amount outside 2–4 years, a diagnostic tolerance around the approximate three-year description. This cutoff identifies a concern; it is not proof those 350 records are erroneous. Eleven ages decline and 86 remain unchanged.

{table(cohort.reset_index())}

The differences are systematically cohort-dependent: A2020 mostly +2/+3, A2022 mostly +0/+1, B2018 mostly +4/+5. Application year plus age difference equals 2022 or 2023 for 1,477 of 1,549 comparable records (95.4%). This pattern is compatible with a common follow-up period, but ages do not identify exact survey dates and this is an inference, not a correction. It is inconsistent with treating every cohort's follow-up as an identical three-year exposure window. Clarify the timing with the data provider; report cohort-specific results and avoid a uniform three-year causal interpretation.

The 11 definitely inconsistent chronological age pairs are:

{table(ages)}

Recommended treatment: preserve both original reports and issue flags; never overwrite age by adding/subtracting three. Retain applicants' valid outcomes. Baseline age may be an optional pretreatment covariate, with explicit missing indicator; follow-up age should not be a main control. An age-flag exclusion can be a sensitivity analysis but risks discarding nearly the entire recent cohort and is not a preferred primary sample definition. Cohort fixed effects address baseline level differences, not unequal follow-up duration or validity of suspect age values.

## Grade measurement conflicts

Fourteen applicants have highest-grade and completion-indicator conflicts (6 treated? see IDs/arm below; counts calculated in the issue files). For all 14, all three completion flags equal zero despite highest grade at least 6. Thirteen conflict for grades 6, 7 and 8; ID 100734 conflicts only for grade 6. No completion flags violate nesting and no repetition-count variables disagree with their corresponding binary measures.

{table(grades)}

The correct measurement is unknowable from the supplied fields. Preserve reported primary highest grade, flag these records and compare results excluding them; alternatively present a clearly labeled clean-grade analysis with contradictory measurements marked missing and raw-grade sensitivity. Do not silently recode all flags from highest grade or vice versa. Missing completion flags alone are not contradictions.

## Parent-age and work inconsistencies

Five parents are reported as no older than the applicant:

{table(parents)}

In `parent_age_clean_derivative.csv` only those five impossible parent-age cells are set to missing, with originals retained. Two additional low but positive parent-child gaps are flagged for review: ID 100614 has mother age 26 and applicant age 15 (gap 11); ID 101047 has father age 19 and applicant age 15 (gap 4). Three gaps above 60 are flagged as unusual (not automatically corrected). Parents' survey-reported characteristics are unnecessary for the primary lottery comparison.

ID 100767 reports working=0 but hours_worked=4. Preserve both reports and check work-related results with this one record excluded. Thirty-two applicants report working=1 with zero weekly hours; temporary absence or different reference windows could explain this, so retain these zeros and disclose them. No positive private-enrollment responses coexist with explicit nonenrollment.

## Missingness and duration

Neighborhood is observed for 897 A2020 applicants, missing for 279 A2020 applicants, and absent for all 277 A2022 and 165 B2018 applicants. The missingness is therefore strongly cohort-patterned; do not use complete-case neighborhood adjustment on the full sample. Baseline socioeconomic stratum is missing in 279 records, parental schooling/income much more often than core outcomes. Treat missing values as missing, not zero; outcome-specific analyses should report the observed N and missingness by lottery arm. Pre-treatment covariate imputation, if used only for precision, should be outcome-blind and paired with missingness indicators. Do not impute missing outcomes as nonenrollment or no repetition.

Core outcome item missingness: enrollment 11, private attendance 18, highest grade 0, ever repeated 8 and total repetitions 8. All missingness by cohort and selection arm is in `missingness_by_cohort_arm.csv`. No applicant is dropped wholesale merely for a missing covariate.

There are 176 records with `years_in_school` 5 or 6, unusually long under a uniform approximately three-year reading. Many respondents' reported completed years also exceed the change in reported age. Given the broader timing ambiguity and uncertain school-year counting convention, retain and flag; prioritize direct highest grade and repetition outcomes, and do not impose a guessed duration cap.

## Nonzero diagnostic counts

{table(issues.loc[issues.n.gt(0),['issue','n','certainty']])}

Counts overlap. A flag marks a review concern or known cross-field contradiction, not automatically an applicant to remove. This audit makes no outcome corrections except the explicitly identified parent-age derivative.
'''.replace('(6 treated? see IDs/arm below; counts calculated in the issue files)', f'({int(d.loc[d.flag_any_grade_contradiction.eq(1), "selected"].sum())} selected and {int(d.flag_any_grade_contradiction.sum()-d.loc[d.flag_any_grade_contradiction.eq(1), "selected"].sum())} not selected)')


if __name__ == '__main__':
    main()
