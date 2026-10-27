"""Phase 3, exploratory: the positive control under MO-ELA's leaky protocol (2026-10-27).

algorithm_selection_control.py splits by problem, so a target's problem is never in training. MO-ELA
splits rows (function x dimension x sample size x seed) at random, so other samples of the target's
own function are in training. This script repeats that protocol on our 185 samples (37 problems x 5
LHS samples): 100 random 80/20 splits of the rows, seed 20261027.

Two tasks, same rows and splits:
- algorithm selection among default NSGA-II, MOEA/D and IBEA (repaired), as in the control:
  sbs, nn1, knn3, rf_class and rf_regr, all trained on the training rows;
- configuration transfer among the c*_P of the problems present in training: sbs (best mean over
  the training rows), landscape_1nn (c*_P of the nearest training row) and oracle (best on target).
Rows are robust-scaled by the training rows' median and IQR; features undefined in any sample are
dropped. Also reported: the share of test rows whose nearest training row is the same problem.

Not pre-registered. Run locally:
    MOLA_PHASE3_MATRIX=... python research/phase3/scripts/algorithm_selection_leaky.py
Adds "leaky_sample_split" to data/algorithm_selection_control.json. scikit-learn 1.9.1.
"""

import json

import analyze_transfer as at
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

ALGORITHMS = ["default__nsgaii", "default__moead", "default__ibea"]
TOLERANCE, SPLITS, SEED, TRAIN_FRACTION = 0.01, 100, 20261027, 0.8


def main() -> None:
    problems = at.pilot_problems()
    hvn = at.hvn_matrix(problems)
    index = {p: i for i, p in enumerate(problems)}
    samples = pd.read_csv(at.PRIMARY_FEATURES)
    features = [c for c in samples.columns if c not in at.META]
    values = samples[features].to_numpy(float)
    defined = np.isfinite(values).all(axis=0)
    values = values[:, defined]
    problem_of = samples["problem"].map(index).to_numpy()
    algorithm_perf = np.array([[hvn[(a, p)].mean() for a in ALGORITHMS] for p in problems])
    # config_perf[a, b]: mean HVn of c*_a on problem b
    config_perf = np.array([[hvn[(f"tuned__{a}", b)].mean() for b in problems] for a in problems])

    rng = np.random.default_rng(SEED)
    rows = []
    for split in range(SPLITS):
        order = rng.permutation(len(values))
        cut = int(round(TRAIN_FRACTION * len(order)))
        train, test = order[:cut], order[cut:]
        q75, median, q25 = np.percentile(values[train], [75, 50, 25], axis=0)
        iqr = q75 - q25
        usable = iqr > 0
        z = (values[:, usable] - median[usable]) / iqr[usable]
        distance = np.linalg.norm(z[test][:, None, :] - z[train][None, :, :], axis=2)
        nearest = np.argsort(distance, axis=1, kind="stable")

        train_problems = problem_of[train]
        labels = np.argmax(algorithm_perf[train_problems], axis=1)
        classifier = RandomForestClassifier(n_estimators=500, random_state=0, n_jobs=-1).fit(
            values[train], labels
        )
        class_pick = classifier.classes_[np.argmax(classifier.predict_proba(values[test]), axis=1)]
        regr_pick = np.argmax(
            np.column_stack(
                [
                    RandomForestRegressor(n_estimators=500, random_state=0, n_jobs=-1)
                    .fit(values[train], algorithm_perf[train_problems, a])
                    .predict(values[test])
                    for a in range(len(ALGORITHMS))
                ]
            ),
            axis=1,
        )
        sbs_algorithm = int(np.argmax(algorithm_perf[train_problems].mean(axis=0)))
        donors = np.unique(train_problems)
        sbs_config = donors[np.argmax(config_perf[donors][:, train_problems].mean(axis=1))]

        for i, row in enumerate(test):
            t = problem_of[row]
            first = train_problems[nearest[i, 0]]
            three = train_problems[nearest[i, :3]]
            picks = {
                "sbs": sbs_algorithm,
                "nn1": int(np.argmax(algorithm_perf[first])),
                "knn3": int(np.argmax(algorithm_perf[three].mean(axis=0))),
                "rf_class": int(class_pick[i]),
                "rf_regr": int(regr_pick[i]),
            }
            entry = {
                "split": split,
                "target": problems[t],
                "vbs": algorithm_perf[t].max(),
                "same_problem_nearest": bool(first == t),
                "cfg_sbs": config_perf[sbs_config, t],
                "cfg_landscape_1nn": config_perf[first, t],
                "cfg_oracle": config_perf[donors, t].max(),
            }
            for name, pick in picks.items():
                entry[name] = algorithm_perf[t, pick]
                entry[f"{name}_hit"] = bool(algorithm_perf[t, pick] >= entry["vbs"] - TOLERANCE)
            rows.append(entry)
    long = pd.DataFrame(rows)

    methods = ["sbs", "nn1", "knn3", "rf_class", "rf_regr"]
    gap = long["vbs"].mean() - long["sbs"].mean()
    cfg_gap = long["cfg_oracle"].mean() - long["cfg_sbs"].mean()
    result = {
        "note": "Exploratory, not pre-registered. Random 80/20 over sample rows, as in MO-ELA.",
        "features_used": int(defined.sum()),
        "same_problem_nearest": round(float(long["same_problem_nearest"].mean()), 3),
        "algorithm_selection_defaults": {
            "vbs_minus_sbs": round(float(gap), 4),
            **{
                m: {
                    "mean_hvn": round(float(long[m].mean()), 4),
                    "closed_gap": round(float((long[m].mean() - long["sbs"].mean()) / gap), 3),
                    "accuracy": round(float(long[f"{m}_hit"].mean()), 3),
                }
                for m in methods
            },
        },
        "configuration_transfer_tuned": {
            "oracle_minus_sbs": round(float(cfg_gap), 4),
            **{
                m: {
                    "mean_hvn": round(float(long[f"cfg_{m}"].mean()), 4),
                    "closed_gap": round(
                        float((long[f"cfg_{m}"].mean() - long["cfg_sbs"].mean()) / cfg_gap), 3
                    ),
                }
                for m in ["sbs", "landscape_1nn", "oracle"]
            },
        },
    }
    path = at.DATA_DIR / "algorithm_selection_control.json"
    stored = json.loads(path.read_text())
    stored["leaky_sample_split"] = result
    path.write_text(json.dumps(stored, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
