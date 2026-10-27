"""Phase 3, exploratory positive control (not pre-registered; 2026-10-27).

Question: the feature-based selection of MO-ELA and Liefooghe et al. works; our configuration
transfer does not. Is that our features and pipeline, or the task? Here the same features, problems
and splits are used for their task: algorithm selection among default-configured algorithms.

Portfolio: default NSGA-II, MOEA/D and IBEA (repaired), already in the phase 3 matrix.
Selectors, all trained on the split's training problems only:
- sbs: the algorithm with the best mean HVn over the training problems;
- nn1: the best algorithm on the nearest training problem (pre-registered landscape distance);
- knn3: the algorithm with the best mean HVn over the 3 nearest training problems;
- rf_class: a random forest classifier (500 trees) of the best algorithm, trained on every sample
  of every training problem;
- rf_regr: one random forest regressor of HVn per algorithm, then the argmax;
- vbs: the best algorithm on the target (oracle).
Metrics, over targets (each averaged over its 5 samples):
- mean HVn;
- closed gap = (selector - SBS) / (VBS - SBS), on the means, as in ASlib;
- accuracy, the share of target samples whose pick is the VBS or within 0.01 of it.
For contrast, the same metrics for the transfer portfolio (37 tuned configurations), from
data/transfer_long.csv.

Run locally:  MOLA_PHASE3_MATRIX=... python research/phase3/scripts/algorithm_selection_control.py
Writes data/algorithm_selection_control.json. scikit-learn 1.9.1.
"""

import json

import analyze_transfer as at
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

ALGORITHMS = ["default__nsgaii", "default__moead", "default__ibea"]
TOLERANCE = 0.01


def main() -> None:
    problems = at.pilot_problems()
    group, family = at.groups_and_families(problems)
    samples = pd.read_csv(at.PRIMARY_FEATURES)
    ctx = at.Context(
        problems,
        samples,
        pd.read_csv(at.RAW_OBJECTIVE_FEATURES),
        at.metadata(problems),
        at.hvn_matrix(problems),
    )
    hvn = at.hvn_matrix(problems)
    index = {p: i for i, p in enumerate(problems)}
    perf = np.array(
        [[hvn[(a, p)].mean() for a in ALGORITHMS] for p in problems]
    )  # problem x algorithm

    rows = []
    for split, unit, targets, train in at.splits(problems, group, family):
        train_index = np.array([index[p] for p in train])
        train_perf = perf[train_index]
        sbs = int(np.argmax(train_perf.mean(axis=0)))
        rows_mask = np.isin(ctx.sample_problem, train_index)
        x_train = ctx.sample_values[rows_mask]
        keep = np.isfinite(x_train).all(axis=0)
        x_train = x_train[:, keep]
        y_problem = ctx.sample_problem[rows_mask]
        labels = np.argmax(perf[y_problem], axis=1)
        classifier = RandomForestClassifier(n_estimators=500, random_state=0, n_jobs=8).fit(
            x_train, labels
        )
        regressors = [
            RandomForestRegressor(n_estimators=500, random_state=0, n_jobs=8).fit(
                x_train, perf[y_problem, a]
            )
            for a in range(len(ALGORITHMS))
        ]
        for target in targets:
            t = index[target]
            for row in np.flatnonzero(ctx.sample_problem == t):
                z_train, z_query = at._robust_z(
                    ctx.sample_values,
                    ctx.means,
                    ctx.sample_problem,
                    ctx.sample_values[row],
                    train_index,
                )
                order = np.argsort(np.linalg.norm(z_train - z_query, axis=1), kind="stable")
                query = np.nan_to_num(ctx.sample_values[row][keep])[None, :]
                class_of = classifier.classes_
                picks = {
                    "sbs": sbs,
                    "nn1": int(np.argmax(train_perf[order[0]])),
                    "knn3": int(np.argmax(train_perf[order[:3]].mean(axis=0))),
                    "rf_class": int(class_of[np.argmax(classifier.predict_proba(query)[0])]),
                    "rf_regr": int(np.argmax([r.predict(query)[0] for r in regressors])),
                }
                best = perf[t].max()
                entry = {"split": split, "unit": unit, "target": target, "vbs": best}
                for name, pick in picks.items():
                    entry[name] = perf[t, pick]
                    entry[f"{name}_hit"] = bool(perf[t, pick] >= best - TOLERANCE)
                rows.append(entry)
    long = pd.DataFrame(rows)

    def summarize(frame, methods, sbs="sbs", vbs="vbs"):
        per_target = (
            frame.groupby(["split", "unit", "target"])[methods + [vbs]].mean().reset_index()
        )
        out = {}
        for split, x in per_target.groupby("split"):
            gap = x[vbs].mean() - x[sbs].mean()
            out[split] = {"vbs_minus_sbs": round(float(gap), 4)}
            for m in methods:
                out[split][m] = {
                    "mean_hvn": round(float(x[m].mean()), 4),
                    "closed_gap": round(float((x[m].mean() - x[sbs].mean()) / gap), 3)
                    if gap > 0
                    else None,
                }
        return out

    methods = ["sbs", "nn1", "knn3", "rf_class", "rf_regr"]
    result = {
        "note": "Exploratory, not pre-registered.",
        "algorithm_selection_defaults": summarize(long, methods),
        "algorithm_selection_accuracy": {
            s: {m: round(float(x[f"{m}_hit"].mean()), 3) for m in methods}
            for s, x in long.groupby("split")
        },
        "best_default_counts": dict(
            zip(ALGORITHMS, np.bincount(np.argmax(perf, axis=1), minlength=3).tolist(), strict=True)
        ),
        "mean_hvn_defaults": dict(
            zip(ALGORITHMS, perf.mean(axis=0).round(4).tolist(), strict=True)
        ),
    }
    transfer = pd.read_csv(at.DATA_DIR / "transfer_long.csv")
    result["configuration_transfer_tuned"] = summarize(
        transfer, ["sbs", "metadata_1nn", "landscape_1nn", "knn_selector"], vbs="oracle"
    )
    (at.DATA_DIR / "algorithm_selection_control.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
