"""Optional package metadata refresh; Python standard library only."""
from pathlib import Path
import csv, hashlib

root=Path(__file__).resolve().parents[1]
dest=root/'documentation'
with (dest/'raw_sha256.csv').open('w',newline='') as out:
    w=csv.writer(out);w.writerow(['file','bytes','sha256'])
    for p in sorted((root/'data/raw').glob('*.csv')):
        w.writerow([p.name,p.stat().st_size,hashlib.sha256(p.read_bytes()).hexdigest()])
with (root/'data/raw/data_dictionary.csv').open() as f:
    lookup={r['Variable']:r for r in csv.DictReader(f)}
lookup['survey_month']=dict(lookup['interview_month'],Description='Actual name in data. Assumed alias of dictionary interview_month; no survey year supplied.')
with (root/'data/derived/adjusted_analysis_data.csv').open() as f:
    cols=next(csv.reader(f))
meaning={
 'cohort':'Municipality and application-year lottery stratum, A_2020/A_2022/B_2018.',
 'age_change':'Recorded followup age minus recorded baseline age. Missing if either missing.',
 'age_unverifiable':'At least one source age is missing.',
 'age_decreased':'Observed survey age is below baseline age.',
 'age_unchanged':'Observed survey age equals baseline age.',
 'age_outside_2_to_4':'Observed age difference below2 or above4. Diagnostic tolerance, not automatic error.',
 'age_at_survey_clean':'Raw survey age except missing for the11 declining-age pairs. No attribution of which source age is wrong.',
 'mother_child_age_gap':'Raw mother age minus raw child survey age.',
 'father_child_age_gap':'Raw father age minus raw child survey age.',
 'mother_age_clean':'Raw mother age except missing where no greater than observed child survey age.',
 'father_age_clean':'Raw father age except missing where no greater than observed child survey age.',
 'grade_conflict':'At least one observed finished_g6/g7/g8 disagrees with highest_grade threshold.',
 'repeats_conflict':'repeats_g6 exceeds total_repeats or ever_repeated disagrees with total_repeats>0.',
 'private_school_conflict':'Private school=1 and current school enrollment=0.',
 'primary_logic_flag':'Union of grade, repetition, and private/enrollment contradictions;14 applicants in supplied data.',
 'work_hours_conflict':'working=0 with positive weekly hours.',
 'grade_below_5_review':'Highest grade below5, unusual under assumed grade6 entry; retain and test exclusion.',
 'school_years_below_grade_progress_review':'years_in_school < highest_grade-5 assuming grade5 completed at entry; retain.',
 'years_in_school_above_4':'Recorded school years above4, a review screen given approximate3y statement; retain.',
 'years_in_school_exceeds_age_gap_plus_1':'Reported school years exceed observed age change+1; review only, uncertain definitions.',
 'mother_age_gap_over_60':'Mother age minus child survey age above60; review only.',
 'father_age_gap_over_60':'Father age minus child survey age above60; review only.'
}
rows=[]
for col in cols:
    if col in lookup: role='Original';desc=lookup[col]['Description']
    else:
        role='Derived';desc=meaning.get(col,'')
        if not desc:
            if col.endswith('_c'):desc='Within-full-cohort centered value of '+col[:-2]+'. Used in baseline-adjusted sensitivity with assignment interactions.'
            elif col.endswith('_imp'):desc='Baseline '+col[:-4]+' with missing values replaced by full within-cohort mean, without outcomes or assignment.'
            elif col.endswith('_missing'):desc='1 if source '+col[:-8]+' missing,0 otherwise.'
            elif col.endswith('_clean'):desc='Raw '+col[:-6]+' except documented-domain violations set missing. No violations detected in supplied data.'
            elif col.startswith('finished_g') and col.endswith('_conflict'):desc='Observed completion indicator differs from highest_grade>=specified grade.'
            else:raise ValueError('Undefined derived variable '+col)
    rows.append([col,role,desc])
with (dest/'analysis_variable_dictionary.csv').open('w',newline='') as out:
    w=csv.writer(out);w.writerow(['variable','role','definition']);w.writerows(rows)
print(f'Documented {len(rows)} variables and source hashes.')
transition_meaning = {
 'history_g6_g7_current':'Reported private-school indicators at G6 entry, G7 entry and followup; ? denotes missing.',
 'g6_private_current_nonprivate':'Observed G6 private=1 and current private=0. Descriptive history, not a counterfactual defier.',
 'ever_g6_g7_private_current_nonprivate':'G6 or G7 private=1 and current private=0; missing original statuses remain missing.',
 'current_status':'Current enrollment response; no inference of dropout versus school completion.'
}
with (root/'data/derived/private_school_transitions.csv').open() as stream:
    tr_columns=next(csv.reader(stream))
definitions={r[0]:r[2] for r in rows}
with (dest/'transition_variable_dictionary.csv').open('w',newline='') as out:
    w=csv.writer(out);w.writerow(['variable','definition'])
    for col in tr_columns:
        definition=transition_meaning.get(col,definitions.get(col))
        if not definition:raise ValueError('Undefined transition variable '+col)
        w.writerow([col,definition])
