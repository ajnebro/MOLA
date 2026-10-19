"""Phase 2, stage A analysis (descriptive, pre-registered in preregistration.md section 7).

Reads data/pilot_features.csv (37 pilot problems x 5 LHS samples) and reports:
- per feature: undefined frequency, within-problem vs between-problem standard deviation and the
  share of variance between problems (an ICC-like ratio);
- recognition: whether each sample's nearest other sample belongs to the same problem;
- donor stability: whether a problem's nearest problem from another formulation group is the
  same for all 5 samples;
- characterization cost against n and D.
Distances use the features defined in every sample, robust-scaled (median, interquartile range).

Run:  python research/phase2/scripts/analyze_stability.py
Writes data/stability_features.csv and data/stability_summary.json.
"""

import json

import numpy as np
import pandas as pd

from common import DATA, PHASE

META = {"problem", "seed", "n", "D", "M", "geometry", "k", "nd_count", "evaluation_seconds",
        "characterization_seconds", "undefined"}


def main() -> None:
    frame = pd.read_csv(DATA / "pilot_features.csv")
    group_of = pd.read_csv(PHASE / "catalogue.csv").set_index("problem")["group"].to_dict()
    features = [c for c in frame.columns if c not in META]

    rows = []
    for name in features:
        values = frame[["problem", name]]
        undefined = int(values[name].isna().sum())
        defined = values.dropna()
        within = defined.groupby("problem")[name].var(ddof=1).mean()
        between = defined.groupby("problem")[name].mean().var(ddof=1)
        rows.append({"feature": name, "undefined_samples": undefined,
                     "within_sd": float(np.sqrt(within)) if pd.notna(within) else np.nan,
                     "between_sd": float(np.sqrt(between)) if pd.notna(between) else np.nan,
                     "between_share": float(between / (between + within))
                     if pd.notna(within) and pd.notna(between) and (between + within) > 0 else np.nan})
    per_feature = pd.DataFrame(rows)
    per_feature.to_csv(DATA / "stability_features.csv", index=False)

    usable = [f for f in features if frame[f].notna().all()]
    matrix = frame[usable].to_numpy(float)
    iqr = np.subtract(*np.percentile(matrix, [75, 25], axis=0))
    keep = iqr > 0
    scaled = (matrix[:, keep] - np.median(matrix[:, keep], axis=0)) / iqr[keep]
    distances = np.linalg.norm(scaled[:, None, :] - scaled[None, :, :], axis=2)
    np.fill_diagonal(distances, np.inf)
    problems = frame["problem"].to_numpy()
    groups = np.array([group_of[p] for p in problems])

    recognized = problems[distances.argmin(axis=1)] == problems
    donors = []
    for i in range(len(frame)):
        other_group = groups != groups[i]
        j = np.flatnonzero(other_group)[distances[i, other_group].argmin()]
        donors.append(problems[j])
    frame["nearest_other_group"] = donors
    stability = frame.groupby("problem")["nearest_other_group"].agg(
        lambda s: s.value_counts().iloc[0] / len(s))
    distinct = frame.groupby("problem")["nearest_other_group"].nunique()

    causes = {}
    for text in frame["undefined"]:
        for feature, cause in json.loads(text).items():
            causes.setdefault(feature, {}).setdefault(cause, 0)
            causes[feature][cause] += 1

    cost = frame.groupby("D")[["n", "evaluation_seconds", "characterization_seconds"]].median()
    summary = {
        "samples": len(frame), "problems": int(frame.problem.nunique()),
        "features_defined_everywhere": len(usable), "features_used_for_distances": int(keep.sum()),
        "recognition_rate_1nn": float(recognized.mean()),
        "donor_modal_share_mean": float(stability.mean()),
        "problems_with_same_donor_in_all_5": int((stability == 1.0).sum()),
        "distinct_donors_per_problem_median": float(distinct.median()),
        "between_share_median": float(per_feature.between_share.median()),
        "features_with_between_share_below_0.5": per_feature.loc[per_feature.between_share < 0.5, "feature"].tolist(),
        "undefined_causes": causes,
        "nd_count_median_by_problem_min": int(frame.groupby("problem").nd_count.median().min()),
        "cost_by_D": cost.round(3).reset_index().to_dict(orient="records"),
    }
    (DATA / "stability_summary.json").write_text(json.dumps(summary, indent=2, default=float) + "\n")
    print(json.dumps({k: v for k, v in summary.items() if k not in ("undefined_causes", "cost_by_D")}, indent=2))
    print(per_feature.sort_values("between_share").head(10).round(3).to_string())


if __name__ == "__main__":
    main()
