"""Independent private-school history audit using only Python's standard library.

Run from any folder: python3 /path/to/transition_audit.py
Raw inputs are never modified. Empty cells stay empty/unknown, never zero.
"""
import csv
import json
from collections import Counter
from pathlib import Path
from statistics import mean, median

HERE = Path(__file__).resolve().parent
RAW = HERE.parent / "data" / "raw"


def read(name):
    with (RAW / name).open(newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write(name, rows, fields=None):
    if fields is None:
        fields = list(rows[0])
    with (HERE / name).open("w", newline="", encoding="utf-8") as stream:
        out = csv.DictWriter(stream, fieldnames=fields)
        out.writeheader()
        out.writerows(rows)


b = read("study_baseline.csv")
f = read("study_followup.csv")
assert len({r["applicant_id"] for r in b}) == len(b)
assert len({r["applicant_id"] for r in f}) == len(f)
assert {r["applicant_id"] for r in b} == {r["applicant_id"] for r in f}
bi = {r["applicant_id"]: r for r in b}
d = [dict(bi[r["applicant_id"]], **r) for r in f]
for r in d:
    r["cohort"] = r["municipality"] + r["application_year"]
    r["private_history_g6_g7_current"] = "->".join(
        r[v] or "unknown" for v in
        ["started_g6_private", "started_g7_private", "in_private_now"])
    # Missing private status stays unknown. '0' at G7 does not establish that
    # grade 7 was reached: these binary fields lack a not-yet-reached category.
    r["g6_to_current_exit"] = (
        "1" if r["in_private_now"] == "0" else "0"
    ) if r["started_g6_private"] == "1" and r["in_private_now"] in ["0", "1"] else ""
    r["g6_to_g7_nonprivate_start"] = (
        "1" if r["started_g7_private"] == "0" else "0"
    ) if r["started_g6_private"] == "1" and r["started_g7_private"] in ["0", "1"] else ""
    earlier_private = r["started_g6_private"] == "1" or r["started_g7_private"] == "1"
    r["earlier_private_to_current_exit"] = (
        "1" if r["in_private_now"] == "0" else "0"
    ) if earlier_private and r["in_private_now"] in ["0", "1"] else ""
    r["g6_private_g7_nonprivate_current_private"] = str(int(
        r["started_g6_private"] == "1" and
        r["started_g7_private"] == "0" and r["in_private_now"] == "1"))
    r["current_exit_schooling_status"] = (
        {"1": "enrolled_nonprivate", "0": "not_currently_enrolled"}.get(
            r["in_school_now"], "current_enrollment_unknown")
        if r["earlier_private_to_current_exit"] == "1" else "not_an_observed_current_exit")
    r["age_change"] = (
        str(float(r["age_at_survey"]) - float(r["age_at_application"]))
        if r["age_at_survey"] and r["age_at_application"] else "")

d.sort(key=lambda r: int(r["applicant_id"]))
write("all_records_with_history.csv", d)
write("all_observed_private_exit_records.csv", [r for r in d if
    r["g6_to_g7_nonprivate_start"] == "1" or r["earlier_private_to_current_exit"] == "1"])
write("selected_current_private_exit_records.csv", [r for r in d if
    r["selected"] == "1" and r["earlier_private_to_current_exit"] == "1"])
write("g6_private_g7_nonprivate_current_private_records.csv", [r for r in d if
    r["g6_private_g7_nonprivate_current_private"] == "1"])

counts, histories, missing, means, years = [], [], [], [], []
for cohort in ["A2020", "A2022", "B2018"]:
    for selected in ["0", "1"]:
        rows = [r for r in d if r["cohort"] == cohort and r["selected"] == selected]
        result = {"cohort": cohort, "selected": selected, "all_applicants": len(rows)}
        for prefix, start, end in [
            ("g6_to_current", "started_g6_private", "in_private_now"),
            ("g6_to_g7", "started_g6_private", "started_g7_private"),
            ("g7_to_current", "started_g7_private", "in_private_now")]:
            starts = [r for r in rows if r[start] == "1"]
            obs = [r for r in starts if r[end] in ["0", "1"]]
            exits = [r for r in obs if r[end] == "0"]
            result[prefix + "_start_private_n"] = len(starts)
            result[prefix + "_end_unknown_n"] = len(starts) - len(obs)
            result[prefix + "_observed_denominator"] = len(obs)
            result[prefix + "_exit_n"] = len(exits)
            result[prefix + "_exit_pct"] = 100 * len(exits) / len(obs) if obs else ""
            if end == "in_private_now":
                for value, label in [("1", "still_enrolled"), ("0", "not_enrolled"), ("", "enrollment_unknown")]:
                    result[prefix + "_exit_" + label] = sum(r["in_school_now"] == value for r in exits)
        earlier = [r for r in rows if r["earlier_private_to_current_exit"] in ["0", "1"]]
        exits = [r for r in earlier if r["earlier_private_to_current_exit"] == "1"]
        result["ever_g6_or_g7_private_current_observed_n"] = len(earlier)
        result["ever_g6_or_g7_private_current_exit_n"] = len(exits)
        result["ever_g6_or_g7_private_current_exit_pct"] = 100 * len(exits) / len(earlier)
        result["g6_private_g7_nonprivate_current_private_n"] = sum(
            r["g6_private_g7_nonprivate_current_private"] == "1" for r in rows)
        counts.append(result)
        for history, n in sorted(Counter(r["private_history_g6_g7_current"] for r in rows).items()):
            histories.append({"cohort": cohort, "selected": selected,
                              "history_g6_g7_current": history, "n": n,
                              "denominator_all_applicants": len(rows)})
        for field in ["started_g6_private", "started_g7_private", "in_private_now", "in_school_now", "receiving_aid_now", "years_in_school"]:
            values = [float(r[field]) for r in rows if r[field]]
            missing.append({"cohort": cohort, "selected": selected, "variable": field,
                            "missing_n": len(rows) - len(values), "all_applicants": len(rows)})
            means.append({"cohort": cohort, "selected": selected, "variable": field,
                          "mean_observed": mean(values), "observed_n": len(values),
                          "min": min(values), "max": max(values)})
        for r in rows:
            if r["years_in_school"]:
                y = float(r["years_in_school"])
                g = float(r["highest_grade"])
                years.append({"applicant_id": r["applicant_id"], "cohort": cohort,
                    "selected": selected, "years_in_school": r["years_in_school"],
                    "highest_grade": r["highest_grade"], "total_repeats": r["total_repeats"],
                    "years_minus_highest_grade_plus5": y - (g - 5),
                    "age_at_application": r["age_at_application"],
                    "age_at_survey": r["age_at_survey"], "age_change": r["age_change"],
                    "exceeds_4_years": int(y > 4),
                    "exceeds_age_change_plus1": int(y > float(r["age_change"]) + 1) if r["age_change"] else ""})

write("transition_counts_by_cohort_arm.csv", counts)
write("history_counts_by_cohort_arm.csv", histories)
write("history_missingness_by_cohort_arm.csv", missing)
write("private_and_school_year_means_by_cohort_arm.csv", means)
write("school_year_counting_diagnostics.csv", years)
summary = {
    "all_applicants": len(d),
    "g6_private_to_current_nonprivate_n": sum(r["g6_to_current_exit"] == "1" for r in d),
    "ever_g6_g7_private_to_current_nonprivate_n": sum(r["earlier_private_to_current_exit"] == "1" for r in d),
    "selected_ever_g6_g7_private_to_current_nonprivate_n": sum(r["earlier_private_to_current_exit"] == "1" and r["selected"] == "1" for r in d),
    "g6_private_g7_nonprivate_current_private_n": sum(r["g6_private_g7_nonprivate_current_private"] == "1" for r in d),
    "current_private_but_not_enrolled_n": sum(r["in_private_now"] == "1" and r["in_school_now"] == "0" for r in d),
    "school_years_missing_n": len(d) - len(years),
    "school_years_exceed4_n": sum(r["exceeds_4_years"] for r in years),
    "school_year_count_minus_highest_grade_plus5_distribution": dict(sorted(Counter(
        r["years_minus_highest_grade_plus5"] for r in years).items())),
}
(HERE / "audit_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(summary, indent=2))
