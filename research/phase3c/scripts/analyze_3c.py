"""Phase 3c, pre-registered analysis (preregistration.md): configuration transfer on bbob-biobj.

Inputs
- The performance matrix (MATRIX/<config>__<problem>.npz, keys s<seed>_e20000):
  - the 55 c*_P (tuned__fNN, P = instance 1 of function NN);
  - the generalists (gen__all, gen__g1-gen__g5);
  - default__nsgaii, default__moead and default__ibea;
  each on the 165 problems (55 functions x instances 1-3, D = 10), seeds 5001-5010.
- MOLA features of each problem from 5 LHS samples (data/features_sample_scaled.csv; geometry
  `bound`, k = D, objective scaling `sample`).

HVn(c, Q): HV of the final front after min-max normalization by COCO's true ideal and nadir
(data/tuning_bounds.json), reference point 1.1, divided by the HV of the union of the final fronts
of every matrix configuration on Q; then the mean over the 10 seeds.

Donors and training sets. A method recommends one of the c*_P whose problem P is in the training
set T (instance-1 problems only). The target is represented by one of its 5 samples (every sample
in turn); a training problem by the mean of its 5 samples.

Splits (similarity between target and donors decreases from S1 to S2):
- S1 near: targets = instances 2 and 3 of every function; T = the 55 instance-1 problems (the
  target's own function is among the donors). Generalist: gen__all.
- S3 function-out: targets = instances 2 and 3 of function f; T = the instance-1 problems of the
  other 54 functions. No tuned generalist (gen__all saw f); secondary.
- S2 group-out: for each bbob function group g (1-5), targets = all instances of the functions
  with a component in g; T = the instance-1 problems of the functions without one. Generalist:
  gen__g<g>.

Methods (as in phase 3 unless stated):
- sbs: the candidate with the best mean HVn over T.
- random: the expected HVn of a uniformly random donor.
- landscape_1nn: the nearest P by Euclidean distance on the robust-scaled features (median and IQR
  over T's samples; features undefined in T or in the target sample, or constant, dropped).
- knn_selector: the candidate with the best mean HVn over the target's 3 nearest problems.
- consensus: the SBS, unless the best candidate on the 3 nearest problems beats the SBS there by at
  least 0.05 in mean HVn (phase 3, report section 11).
- thesis_1nn: the nearest P by the thesis distance over its 19 features.
- loss_predictor: ridge (lambda = 1) on |z(A) - z(B)| over ordered pairs within T.
- References: generalist (the split's gen__*), default (default__nsgaii), oracle (best candidate),
  same_function (S1 and S3 only: the c*_P of the target's own function, when it is in T).
metadata_1nn is not used: every problem has D = 10 and the same bounds, so it cannot tell them apart.

Gates (one-sided Wilcoxon signed-rank tests over the 55 functions, Holm-corrected over the two):
- G4 (S1): HVn(landscape_1nn) > HVn(generalist). A function's value is its mean over its targets
  and samples.
- G5 (S2): HVn(consensus) > HVn(generalist). A function's value is its mean over every fold in which
  it is a target.
A gate passes if the mean difference is positive and the Holm-adjusted p-value is below 0.05.

Run locally:  MOLA_PHASE3C_MATRIX=... python research/phase3c/scripts/analyze_3c.py
Writes data/hvn.csv, data/transfer_long.csv, data/transfer_summary.json and data/gates.json.
"""

import json
import os
from pathlib import Path

import moocore
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
DATA = HERE.parent / "data"
MATRIX = Path(os.environ.get("MOLA_PHASE3C_MATRIX", r"C:\tmp\mola-phase3c\matrix\fronts"))
SEEDS = tuple(range(5001, 5011))
FINAL = 20_000
REFERENCE = 1.1
DELTA, K = 0.05, 3
GENERALISTS = ["gen__all"] + [f"gen__g{g}" for g in range(1, 6)]
DEFAULTS = ["default__nsgaii", "default__moead", "default__ibea"]
META = {
    "problem",
    "seed",
    "n",
    "D",
    "M",
    "geometry",
    "k",
    "nd_count",
    "evaluation_seconds",
    "characterization_seconds",
    "undefined",
    "objective_scaling",
    "mola_version",
}
THESIS19 = [
    "dist_x_avg",
    "dist_x_max",
    "dist_f_avg",
    "dist_f_max",
    "nd_n",
    "dist_x_nd_avg",
    "dist_x_nd_max",
    "rank_avg",
    "rank_max",
    "rank_ent",
    "sup_avg_neig",
    "inf_avg_neig",
    "inc_avg_neig",
    "lnd_avg_neig",
    "lsupp_avg_neig",
    "dist_x_avg_neig",
    "dist_f_avg_neig",
    "dist_x_cor_neig",
    "dist_f_cor_neig",
]
METHODS = [
    "sbs",
    "random",
    "landscape_1nn",
    "knn_selector",
    "consensus",
    "thesis_1nn",
    "loss_predictor",
    "generalist",
    "default",
    "oracle",
    "same_function",
]


def _hv(points, reference):
    points = points[np.all(points < reference, axis=1)]
    return float(moocore.hypervolume(points, ref=reference)) if len(points) else 0.0


def hvn_table(problems, configs, bounds) -> pd.DataFrame:
    reference = np.full(2, REFERENCE)
    rows = []
    for q in problems:
        ideal = np.asarray(bounds[q]["ideal"])
        span = np.asarray(bounds[q]["nadir"]) - ideal
        fronts = {c: np.load(MATRIX / f"{c}__{q}.npz") for c in configs}
        union = np.vstack([fronts[c][f"s{s}_e{FINAL}"] for c in configs for s in SEEDS])
        union = union[moocore.is_nondominated(union, keep_weakly=False)]
        best = _hv((union - ideal) / span, reference)
        for c in configs:
            values = [
                _hv((fronts[c][f"s{s}_e{FINAL}"] - ideal) / span, reference) / best for s in SEEDS
            ]
            rows.append({"config": c, "problem": q, "hvn": float(np.mean(values))})
    return pd.DataFrame(rows)


class Data:
    def __init__(self, catalogue, samples, hvn):
        self.catalogue = catalogue
        self.problems = list(catalogue)
        self.donors = [p for p in self.problems if catalogue[p]["instance"] == 1]
        self.features = [c for c in samples.columns if c not in META]
        self.thesis_columns = [self.features.index(c) for c in THESIS19]
        self.samples = samples.reset_index(drop=True)
        self.values = self.samples[self.features].to_numpy(float)
        self.sample_problem = self.samples.problem.to_numpy()
        self.means = {
            p: np.nanmean(self.values[self.sample_problem == p], axis=0) for p in self.problems
        }
        self.H = hvn.pivot(index="config", columns="problem", values="hvn")

    def config_of(self, donor):
        return f"tuned__f{self.catalogue[donor]['function']:02d}"


def _robust_z(data, train, query):
    rows = data.values[np.isin(data.sample_problem, train)]
    defined = np.isfinite(rows).all(axis=0) & np.isfinite(query)
    q75, median, q25 = np.percentile(rows[:, defined], [75, 50, 25], axis=0)
    iqr = q75 - q25
    keep = np.flatnonzero(defined)[iqr > 0]
    median, iqr = median[iqr > 0], iqr[iqr > 0]
    means = np.vstack([data.means[p] for p in train])
    return (means[:, keep] - median) / iqr, (query[keep] - median) / iqr


def recommend(data, target, row, train, generalist):
    configs = [data.config_of(p) for p in train]
    on_target = data.H.loc[configs, target].to_numpy()
    within = data.H.loc[configs, train].to_numpy()  # within[a, b]: c*_{train[a]} on train[b]
    query = data.values[row]
    z_train, z_query = _robust_z(data, train, query)
    distance = np.linalg.norm(z_train - z_query, axis=1)
    nearest = np.argsort(distance, kind="stable")[:K]
    sbs = int(np.argmax(within.mean(axis=1)))
    advantage = within[:, nearest].mean(axis=1) - within[sbs, nearest].mean()
    best_near = int(np.argmax(advantage))
    consensus = best_near if advantage[best_near] >= DELTA and best_near != sbs else sbs

    means = np.vstack([data.means[p] for p in train])
    a, b = means[:, data.thesis_columns], query[data.thesis_columns]
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(b < a, b / a, a / b)
    thesis = np.nansum(np.abs(1 - ratio), axis=1)

    n = len(train)
    off = ~np.eye(n, dtype=bool)
    x = np.abs(z_train[:, None, :] - z_train[None, :, :])[off]
    y = (np.diag(within)[None, :] - within)[off]
    x_mu, x_sd = x.mean(axis=0), x.std(axis=0)
    x_sd[x_sd == 0] = 1.0
    xs = np.c_[np.ones(len(x)), (x - x_mu) / x_sd]
    penalty = np.eye(xs.shape[1])
    penalty[0, 0] = 0.0
    beta = np.linalg.solve(xs.T @ xs + penalty, xs.T @ y)
    predicted = np.c_[np.ones(n), (np.abs(z_train - z_query) - x_mu) / x_sd] @ beta

    function = data.catalogue[target]["function"]
    same = [i for i, p in enumerate(train) if data.catalogue[p]["function"] == function]
    return {
        "sbs": on_target[sbs],
        "random": float(on_target.mean()),
        "landscape_1nn": on_target[int(np.argmin(distance))],
        "knn_selector": on_target[int(np.argmax(within[:, nearest].mean(axis=1)))],
        "consensus": on_target[consensus],
        "thesis_1nn": on_target[int(np.argmin(thesis))],
        "loss_predictor": on_target[int(np.argmin(predicted))],
        "generalist": float(data.H.loc[generalist, target]) if generalist else np.nan,
        "default": float(data.H.loc["default__nsgaii", target]),
        "oracle": float(on_target.max()),
        "same_function": on_target[same[0]] if same else np.nan,
        "landscape_donor": train[int(np.argmin(distance))],
        "landscape_picks_same_function": bool(
            data.catalogue[train[int(np.argmin(distance))]]["function"] == function
        ),
        "consensus_deviates": bool(consensus != sbs),
    }


def splits(data):
    catalogue = data.catalogue
    for p in data.problems:
        if catalogue[p]["instance"] > 1:
            yield "S1", "all", p, data.donors, "gen__all"
    for p in data.problems:
        if catalogue[p]["instance"] > 1:
            f = catalogue[p]["function"]
            yield (
                "S3",
                f"f{f:02d}",
                p,
                [d for d in data.donors if catalogue[d]["function"] != f],
                None,
            )
    for g in range(1, 6):
        train = [d for d in data.donors if g not in catalogue[d]["groups"]]
        for p in data.problems:
            if g in catalogue[p]["groups"]:
                yield "S2", f"g{g}", p, train, f"gen__g{g}"


def _one_sided(a, b):
    difference = a - b
    p = (
        float(wilcoxon(a, b, alternative="greater").pvalue)
        if (difference.abs() > 1e-12).any()
        else 1.0
    )
    return {
        "mean": float(difference.mean()),
        "median": float(difference.median()),
        "wins_losses_ties": [
            int((difference > 1e-9).sum()),
            int((difference < -1e-9).sum()),
            int((difference.abs() <= 1e-9).sum()),
        ],
        "p": p,
    }


def main() -> None:
    catalogue = json.loads((DATA / "catalogue.json").read_text())
    bounds = json.loads((DATA / "tuning_bounds.json").read_text())
    samples = pd.read_csv(DATA / "features_sample_scaled.csv")
    configs = [f"tuned__f{f:02d}" for f in range(1, 56)] + GENERALISTS + DEFAULTS
    hvn = hvn_table(list(catalogue), configs, bounds)
    hvn.to_csv(DATA / "hvn.csv", index=False)
    data = Data(catalogue, samples, hvn)

    rows = []
    for split, unit, target, train, generalist in splits(data):
        for row in np.flatnonzero(data.sample_problem == target):
            rows.append(
                {
                    "split": split,
                    "unit": unit,
                    "target": target,
                    "function": catalogue[target]["function"],
                    "instance": catalogue[target]["instance"],
                    "sample": int(data.samples.loc[row, "seed"]),
                    **recommend(data, target, row, train, generalist),
                }
            )
    long = pd.DataFrame(rows)
    long.to_csv(DATA / "transfer_long.csv", index=False)

    per_function = long.groupby(["split", "function"])[METHODS].mean().reset_index()
    summary = {}
    for split, x in long.groupby("split"):
        loss = x[METHODS].rsub(x["oracle"], axis=0)
        f = per_function[per_function.split == split]
        summary[split] = {
            "mean_hvn_over_functions": f[METHODS].mean().round(4).to_dict(),
            "median_loss_vs_oracle": loss.median().round(4).to_dict(),
            "share_loss_above_0.10": (loss > 0.10).mean().round(3).to_dict(),
            "landscape_picks_same_function": float(x.landscape_picks_same_function.mean()),
            "consensus_deviates_from_sbs": float(x.consensus_deviates.mean()),
            "landscape_donor_identical_across_samples": float(
                (x.groupby(["unit", "target"]).landscape_donor.nunique() == 1).mean()
            ),
        }
    (DATA / "transfer_summary.json").write_text(json.dumps(summary, indent=2) + "\n")

    s1 = per_function[per_function.split == "S1"].set_index("function")
    s2 = per_function[per_function.split == "S2"].set_index("function")
    g4 = _one_sided(s1["landscape_1nn"], s1["generalist"])
    g5 = _one_sided(s2["consensus"], s2["generalist"])
    ordered = sorted([("G4", g4), ("G5", g5)], key=lambda item: item[1]["p"])
    adjusted, running = {}, 0.0
    for rank, (name, test) in enumerate(ordered):
        running = max(running, min(1.0, test["p"] * (len(ordered) - rank)))
        adjusted[name] = running
    gates = {}
    for name, test in (("G4", g4), ("G5", g5)):
        gates[name] = {
            **test,
            "p_holm": adjusted[name],
            "passes": bool(test["mean"] > 0 and adjusted[name] < 0.05),
        }
    gates["G4"]["rule"] = (
        "S1: landscape_1nn > generalist (gen__all), one-sided Wilcoxon over 55 functions"
    )
    gates["G5"]["rule"] = (
        "S2: consensus > generalist (gen__g<g>), one-sided Wilcoxon over 55 functions"
    )
    (DATA / "gates.json").write_text(json.dumps(gates, indent=2) + "\n")
    print(json.dumps(gates, indent=2))
    print(
        pd.DataFrame({s: v["mean_hvn_over_functions"] for s, v in summary.items()})
        .round(3)
        .to_string()
    )


if __name__ == "__main__":
    main()
