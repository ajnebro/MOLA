"""Phase 3c, amendment 2 (preregistration.md section 9): the positive control under four protocols.

Exploratory, fixed before the matrix exists. Phase 3's control (phase3/report.md, section 12) found
that published feature-based selection succeeds because the target problem is in training: with
MO-ELA's row-level split our features close 79-98% of the gap, and with the target problem left
out no selector beats the SBS. Here the same control runs on bbob-biobj, where similarity is known,
with four protocols from leaky to far:
- rows: 100 random 80/20 splits of the 825 sample rows (165 problems x 5 LHS samples), seed
  20261027, as in MO-ELA;
- instance_out: leave one problem out; the other instances of its function stay in training, as the
  50 sibling problems per generator setting of Liefooghe et al. 2021;
- function_out: leave one function out (its three instances);
- group_out: the five bbob-group folds of S2.

Two tasks, same rows and splits:
- algorithm selection among default NSGA-II, MOEA/D and IBEA: sbs, nn1, knn3, rf_class and rf_regr;
- configuration transfer among the c*_f of the functions present in training: sbs, landscape_1nn,
  knn_selector and oracle.
Neighbours are training rows, robust-scaled by the training rows' median and IQR; features undefined
in any sample are dropped. Random forests have 500 trees and random_state 0.

Reported per protocol, as means over functions (the unit of analysis, as in the gates): mean HVn,
closed gap (method - SBS) / (VBS - SBS) with the absolute gap next to it, accuracy (share of rows
within 0.01 of the VBS) and the share of rows whose nearest training row is the same function.

Run locally after analyze_3c.py:
    python research/phase3c/scripts/positive_control_3c.py
Reads MOLA_PHASE3C_HVN (default data/hvn.csv); writes MOLA_PHASE3C_CONTROL_OUT (default
data/positive_control.json). scikit-learn 1.9.1.
"""

import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
from analyze_3c import DATA, DEFAULTS, META
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

HVN = Path(os.environ.get("MOLA_PHASE3C_HVN", DATA / "hvn.csv"))
OUT = Path(os.environ.get("MOLA_PHASE3C_CONTROL_OUT", DATA / "positive_control.json"))
TOLERANCE, SPLITS, SEED, TRAIN_FRACTION, K = 0.01, 100, 20261027, 0.8, 3
ALGORITHM_METHODS = ["sbs", "nn1", "knn3", "rf_class", "rf_regr"]
CONFIG_METHODS = ["sbs", "landscape_1nn", "knn_selector"]


def protocols(catalogue, problem_of, problems, rng):
    """Yield (protocol, train row mask, test row indices)."""
    rows = len(problem_of)
    for _ in range(SPLITS):
        order = rng.permutation(rows)
        cut = int(round(TRAIN_FRACTION * rows))
        mask = np.zeros(rows, dtype=bool)
        mask[order[:cut]] = True
        yield "rows", mask, order[cut:]
    function_of = np.array([catalogue[problems[p]]["function"] for p in problem_of])
    for p in range(len(problems)):
        yield "instance_out", problem_of != p, np.flatnonzero(problem_of == p)
    for f in sorted(set(function_of)):
        yield "function_out", function_of != f, np.flatnonzero(function_of == f)
    in_group = np.array([catalogue[problems[p]]["groups"] for p in problem_of], dtype=object)
    for g in range(1, 6):
        test = np.array([g in groups for groups in in_group])
        yield "group_out", ~test, np.flatnonzero(test)


def main() -> None:
    catalogue = json.loads((DATA / "catalogue.json").read_text())
    problems = list(catalogue)
    index = {p: i for i, p in enumerate(problems)}
    samples = pd.read_csv(DATA / "features_sample_scaled.csv")
    features = [c for c in samples.columns if c not in META]
    values = samples[features].to_numpy(float)
    defined = np.isfinite(values).all(axis=0)
    values = values[:, defined]
    problem_of = samples["problem"].map(index).to_numpy()
    function_of = np.array([catalogue[p]["function"] for p in problems])

    H = pd.read_csv(HVN).pivot(index="config", columns="problem", values="hvn")
    algorithm_perf = H.loc[DEFAULTS, problems].to_numpy().T  # problem x algorithm
    functions = sorted(set(function_of))
    # config_perf[f, p]: HVn of c*_f (tuned on instance 1 of function f) on problem p
    config_perf = H.loc[[f"tuned__f{f:02d}" for f in functions], problems].to_numpy()
    config_row = {f: i for i, f in enumerate(functions)}

    rng = np.random.default_rng(SEED)
    records = []
    for protocol, train_mask, test in protocols(catalogue, problem_of, problems, rng):
        train = np.flatnonzero(train_mask)
        q75, median, q25 = np.percentile(values[train], [75, 50, 25], axis=0)
        iqr = q75 - q25
        usable = iqr > 0
        z = (values[:, usable] - median[usable]) / iqr[usable]
        distance = np.linalg.norm(z[test][:, None, :] - z[train][None, :, :], axis=2)
        nearest = np.argsort(distance, axis=1, kind="stable")[:, :K]
        train_problems = problem_of[train]

        labels = np.argmax(algorithm_perf[train_problems], axis=1)
        if len(set(labels)) > 1:
            classifier = RandomForestClassifier(n_estimators=500, random_state=0, n_jobs=-1)
            classifier.fit(values[train], labels)
            class_pick = classifier.classes_[
                np.argmax(classifier.predict_proba(values[test]), axis=1)
            ]
        else:
            class_pick = np.full(len(test), labels[0])
        regr_pick = np.argmax(
            np.column_stack(
                [
                    RandomForestRegressor(n_estimators=500, random_state=0, n_jobs=-1)
                    .fit(values[train], algorithm_perf[train_problems, a])
                    .predict(values[test])
                    for a in range(len(DEFAULTS))
                ]
            ),
            axis=1,
        )
        sbs_algorithm = int(np.argmax(algorithm_perf[train_problems].mean(axis=0)))

        candidates = np.array(sorted({config_row[f] for f in function_of[train_problems]}))
        within = config_perf[candidates][:, train_problems]  # candidate x training row
        sbs_config = candidates[np.argmax(within.mean(axis=1))]

        for i, row in enumerate(test):
            t = problem_of[row]
            near = train_problems[nearest[i]]
            knn_config = candidates[np.argmax(config_perf[candidates][:, near].mean(axis=1))]
            picks = {
                "sbs": sbs_algorithm,
                "nn1": int(np.argmax(algorithm_perf[near[0]])),
                "knn3": int(np.argmax(algorithm_perf[near].mean(axis=0))),
                "rf_class": int(class_pick[i]),
                "rf_regr": int(regr_pick[i]),
            }
            vbs = algorithm_perf[t].max()
            record = {
                "protocol": protocol,
                "function": int(function_of[t]),
                "same_function_nearest": bool(function_of[near[0]] == function_of[t]),
                "vbs": vbs,
                "cfg_sbs": config_perf[sbs_config, t],
                "cfg_landscape_1nn": config_perf[config_row[function_of[near[0]]], t],
                "cfg_knn_selector": config_perf[knn_config, t],
                "cfg_oracle": config_perf[candidates, t].max(),
            }
            for name, pick in picks.items():
                record[name] = algorithm_perf[t, pick]
                record[f"{name}_hit"] = float(algorithm_perf[t, pick] >= vbs - TOLERANCE)
            records.append(record)
    long = pd.DataFrame(records)

    result: dict = {"note": "Exploratory (amendment 2), fixed before the matrix existed."}
    for protocol, x in long.groupby("protocol", sort=False):
        f = x.groupby("function").mean(numeric_only=True)
        gap = f["vbs"].mean() - f["sbs"].mean()
        cfg_gap = f["cfg_oracle"].mean() - f["cfg_sbs"].mean()
        result[protocol] = {
            "same_function_nearest": round(float(x["same_function_nearest"].mean()), 3),
            "algorithm_selection_defaults": {
                "vbs_minus_sbs": round(float(gap), 4),
                **{
                    m: {
                        "mean_hvn": round(float(f[m].mean()), 4),
                        "closed_gap": round(float((f[m].mean() - f["sbs"].mean()) / gap), 3)
                        if gap > 0
                        else None,
                        "accuracy": round(float(f[f"{m}_hit"].mean()), 3),
                    }
                    for m in ALGORITHM_METHODS
                },
            },
            "configuration_transfer_tuned": {
                "oracle_minus_sbs": round(float(cfg_gap), 4),
                **{
                    m: {
                        "mean_hvn": round(float(f[f"cfg_{m}"].mean()), 4),
                        "closed_gap": round(
                            float((f[f"cfg_{m}"].mean() - f["cfg_sbs"].mean()) / cfg_gap), 3
                        )
                        if cfg_gap > 0
                        else None,
                    }
                    for m in CONFIG_METHODS
                },
            },
        }
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
