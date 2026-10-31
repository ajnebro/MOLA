"""Phase 3g pre-registered analysis: the recommendation against an irace generalist (D11).

See preregistration.md. The generalist is tuned by irace on the training set.

For every split of phase 3 (LOGO, LOFO, random 80/20 by problem; analyze_transfer.splits) and every
target sample, it takes from phase 3's pipeline (analyze_transfer.recommend, unchanged):
- knn_selector (the method under evaluation), landscape_1nn, random (the ablation control),
  default (default NSGA-II, baseline 2), sbs, oracle and self (ceilings);
and adds:
- generalist (baseline 1): gen__lofo_<family of the target>, tuned by irace on the development
  problems outside that family. Its training set equals the split's in LOFO and is a subset of it
  in LOGO and in the random split (no leakage, a handicap for the generalist there);
- consensus_generalist: the generalist, unless the configuration with the best mean HVn on the
  target's K nearest training problems beats the generalist on those problems by at least DELTA;
- distance_units: the distance to the nearest training problem, in units of resampling noise (the
  median distance between two samples of the same training problem, in the same robust z-space).

HVn of the generalists uses the matrix's normalization (union of the 40 matrix configurations'
final fronts); they do not enter the union, so every phase 3 value is unchanged.

Gate G6 (LOFO, the split where method and baseline see the same training set):
  HVn(knn_selector) > HVn(generalist), one-sided Wilcoxon signed-rank over the 32 formulation
  groups (group value = mean over its targets and samples); passes if the mean difference is
  positive and p < 0.05.

Run locally:
    MOLA_PHASE3_MATRIX=... MOLA_PHASE3G_RAW=... python research/phase3g/scripts/analyze_3g.py
Writes data/generalists_hvn.csv, data/transfer_3g_long.csv, data/summary_3g.json, data/gate_g6.json
(MOLA_PHASE3G_OUT overrides the output directory, for tests).
"""

import itertools
import json
import os
import sys
from pathlib import Path

import moocore
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase3" / "scripts"))

import analyze_transfer as at  # noqa: E402

DATA = HERE.parent / "data"
OUT = Path(os.environ.get("MOLA_PHASE3G_OUT", DATA))
RAW = Path(os.environ.get("MOLA_PHASE3G_RAW", r"C:\tmp\mola-phase3g\matrix")) / "fronts"
K, DELTA, TIE = 3, 0.05, 1e-9
DISTANCE_BINS = [0, 1.5, 3, 6, np.inf]
METHODS = [
    "random",
    "default",
    "generalist",
    "sbs",
    "landscape_1nn",
    "knn_selector",
    "consensus_generalist",
    "oracle",
    "self",
]


def generalist_of(family: str) -> str:
    return f"gen__lofo_{family.lower().replace('/', '')}"


def generalists_hvn(problems: list[str], configs: list[str]) -> pd.DataFrame:
    bounds = json.loads((at.DATA_DIR / "tuning_bounds.json").read_text())
    matrix_configs = [f"tuned__{p}" for p in problems] + list(at.DEFAULTS)
    rows = []
    for problem in problems:
        ideal = np.asarray(bounds[problem]["ideal"])
        span = np.asarray(bounds[problem]["nadir"]) - ideal
        reference = np.full(len(ideal), at.REFERENCE)

        def hv(front, ideal=ideal, span=span, reference=reference):
            scaled = (front - ideal) / span
            scaled = scaled[np.all(scaled < reference, axis=1)]
            return float(moocore.hypervolume(scaled, ref=reference)) if len(scaled) else 0.0

        union = np.vstack(
            [
                np.load(at.MATRIX / f"{c}__{problem}.npz")[f"s{s}_e{at.FINAL}"]
                for c in matrix_configs
                for s in at.SEEDS
            ]
        )
        best = hv(union[moocore.is_nondominated(union, keep_weakly=False)])
        for c in configs:
            fronts = np.load(RAW / f"{c}__{problem}.npz")
            values = [hv(fronts[f"s{s}_e{at.FINAL}"]) / best for s in at.SEEDS]
            rows.append({"config": c, "problem": problem, "hvn": float(np.mean(values))})
    return pd.DataFrame(rows)


def _scaled(ctx, row, train):
    """Training samples, training means and the query, robust-scaled as analyze_transfer does."""
    values = ctx.sample_values
    train_rows = np.isin(ctx.sample_problem, train)
    query = values[row]
    defined = np.isfinite(values[train_rows]).all(axis=0) & np.isfinite(query)
    q75, median, q25 = np.percentile(values[train_rows][:, defined], [75, 50, 25], axis=0)
    iqr = q75 - q25
    keep = np.flatnonzero(defined)[iqr > 0]
    median, iqr = median[iqr > 0], iqr[iqr > 0]
    samples = (values[train_rows][:, keep] - median) / iqr
    means = (ctx.means[train][:, keep] - median) / iqr
    return samples, ctx.sample_problem[train_rows], means, (query[keep] - median) / iqr


def _noise_unit(samples, owner):
    distances = [
        np.linalg.norm(a - b)
        for p in np.unique(owner)
        for a, b in itertools.combinations(samples[owner == p], 2)
    ]
    return float(np.median(distances))


def recommend_3g(ctx, gen_score, target, row, train, generalist):
    """Phase 3 methods plus the generalist, its consensus rule and the nearest distance.

    The distance is to the nearest training problem, in units of resampling noise.
    """
    base = at.recommend(ctx, target, row, train)
    samples, owner, means, query = _scaled(ctx, row, train)
    distance = np.linalg.norm(means - query, axis=1)
    nearest = np.argsort(distance, kind="stable")[:K]
    within = ctx.score[np.ix_(train, train)]  # within[a, b]: c*_{train[a]} on train[b]
    gen_near = gen_score[generalist][train[nearest]].mean()
    advantage = within[:, nearest].mean(axis=1) - gen_near
    best = int(np.argmax(advantage))
    deviates = bool(advantage[best] >= DELTA)
    gen_on_target = float(gen_score[generalist][target])
    return {
        **{m: base[m] for m in ("random", "default", "sbs", "landscape_1nn", "knn_selector")},
        **{m: base[m] for m in ("oracle", "self")},
        "generalist": gen_on_target,
        "consensus_generalist": float(ctx.score[train[best], target])
        if deviates
        else gen_on_target,
        "consensus_deviates": deviates,
        "distance_units": float(distance.min() / _noise_unit(samples, owner)),
    }


def _paired(a: pd.Series, b: pd.Series, alternative: str) -> dict:
    difference = a - b
    p = (
        float(wilcoxon(a, b, alternative=alternative).pvalue)
        if (difference.abs() > TIE).any()
        else 1.0
    )
    return {
        "mean": round(float(difference.mean()), 4),
        "median": round(float(difference.median()), 4),
        "wins_losses_ties": [
            int((difference > TIE).sum()),
            int((difference < -TIE).sum()),
            int((difference.abs() <= TIE).sum()),
        ],
        "p": p,
    }


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
    index = {p: i for i, p in enumerate(problems)}
    configs = sorted({generalist_of(f) for f in family.values()} | {"gen__all"})
    hvn = generalists_hvn(problems, configs)
    OUT.mkdir(parents=True, exist_ok=True)
    hvn.to_csv(OUT / "generalists_hvn.csv", index=False)
    table = hvn.pivot(index="config", columns="problem", values="hvn")
    gen_score = {c: table.loc[c, problems].to_numpy() for c in configs}

    rows = []
    for split, unit, targets, train in at.splits(problems, group, family):
        train_index = np.array([index[p] for p in train])
        for target in targets:
            t = index[target]
            for row in np.flatnonzero(ctx.sample_problem == t):
                rows.append(
                    {
                        "split": split,
                        "unit": unit,
                        "target": target,
                        "group": group[target],
                        "family": family[target],
                        **recommend_3g(
                            ctx, gen_score, t, row, train_index, generalist_of(family[target])
                        ),
                    }
                )
    long = pd.DataFrame(rows)
    long.to_csv(OUT / "transfer_3g_long.csv", index=False)

    def by_group(split):
        x = long[long.split == split]
        per_target = x.groupby(["unit", "target", "group"])[METHODS].mean().reset_index()
        return per_target.groupby("group")[METHODS].mean()

    lofo = by_group("LOFO")
    g6 = _paired(lofo["knn_selector"], lofo["generalist"], "greater")
    gate = {
        "rule": "LOFO: knn_selector > generalist (gen__lofo of the target's family), one-sided "
        "Wilcoxon over the 32 formulation groups, mean difference > 0 and p < 0.05",
        "groups": int(len(lofo)),
        **g6,
        "passes": bool(g6["mean"] > 0 and g6["p"] < 0.05),
    }
    (OUT / "gate_g6.json").write_text(json.dumps(gate, indent=2) + "\n")

    summary = {"note": "G6 is pre-registered; everything else is secondary and descriptive."}
    for split in ("LOFO", "LOGO", "random"):
        x = long[long.split == split]
        per_target = x.groupby(["unit", "target"])[METHODS].mean()
        loss = x[METHODS].rsub(x["oracle"], axis=0)
        groups = by_group(split)
        bins = pd.cut(x["distance_units"], DISTANCE_BINS)
        gain = (x["knn_selector"] - x["generalist"]).groupby(bins, observed=True)
        summary[split] = {
            "mean_hvn_over_targets": per_target.mean().round(4).to_dict(),
            "median_loss_vs_oracle": loss.median().round(4).to_dict(),
            "share_loss_above_0.10": (loss > 0.10).mean().round(3).to_dict(),
            "cvar90_loss": {
                m: round(float(loss[m][loss[m] >= loss[m].quantile(0.9)].mean()), 4)
                for m in METHODS
            },
            "over_groups_two_sided": {
                f"{m}_vs_{b}": _paired(groups[m], groups[b], "two-sided")
                for m, b in [
                    ("knn_selector", "generalist"),
                    ("consensus_generalist", "generalist"),
                    ("knn_selector", "default"),
                    ("knn_selector", "random"),
                    ("generalist", "default"),
                    ("generalist", "sbs"),
                ]
            },
            "consensus_deviates_from_generalist": round(float(x["consensus_deviates"].mean()), 3),
            "knn_minus_generalist_by_distance_units": {
                str(k): {"samples": int(v.size), "mean": round(float(v.mean()), 4)} for k, v in gain
            },
        }
    (OUT / "summary_3g.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(gate, indent=2))
    print(
        pd.DataFrame({s: summary[s]["mean_hvn_over_targets"] for s in ("LOFO", "LOGO", "random")})
    )


if __name__ == "__main__":
    main()
