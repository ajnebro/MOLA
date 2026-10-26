"""Phase 3, exploratory (not pre-registered; step 1 of the plan approved on 2026-10-26).

1. Strata. Every target at 20 000 evaluations is classed by the spread of the 36 tuned donors:
   - easy: the median donor is within 0.01 of the best donor;
   - hard: even the best donor stays below 0.8;
   - intermediate: the rest.
   The classes use the matrix itself, so they are descriptive.
2. Consensus rule. The SBS is the default; another configuration replaces it only when the target's
   k nearest training problems (pre-registered landscape distance) agree that it is better. That is,
   when its mean HVn advantage over the SBS on those k problems is at least delta. Grid fixed before
   running: k in {3, 5}, delta in {0, 0.01, 0.02, 0.05}. With delta = 0 and k = 3 it is the
   knn_selector of the pre-registration.

Run locally:  MOLA_PHASE3_MATRIX=... python research/phase3/scripts/consensus_strata.py
Writes data/consensus_strata.json, data/consensus_long.csv and data/strata.csv.
"""

import json

import analyze_transfer as at
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

GRID = [(k, delta) for k in (3, 5) for delta in (0.0, 0.01, 0.02, 0.05)]
TIE = 1e-9


def strata(ctx, problems):
    rows = []
    for j, q in enumerate(problems):
        donors = ctx.score[[i for i in range(len(problems)) if i != j], j]
        best, median = donors.max(), np.median(donors)
        kind = "easy" if best - median < 0.01 else ("hard" if best < 0.8 else "intermediate")
        rows.append({"target": q, "stratum": kind, "best_donor": best, "median_donor": median})
    return pd.DataFrame(rows).set_index("target")


def consensus(ctx, target, row, train, k, delta):
    """HVn on the target of the consensus recommendation, and whether it left the SBS."""
    within = ctx.score[np.ix_(train, train)]  # within[a, b]: c*_{train[a]} on train[b]
    sbs = int(np.argmax(within.mean(axis=1)))
    z_train, z_query = at._robust_z(
        ctx.sample_values, ctx.means, ctx.sample_problem, ctx.sample_values[row], train
    )
    nearest = np.argsort(np.linalg.norm(z_train - z_query, axis=1), kind="stable")[:k]
    advantage = within[:, nearest].mean(axis=1) - within[sbs, nearest].mean()
    best = int(np.argmax(advantage))
    chosen = best if advantage[best] >= delta and best != sbs else sbs
    return float(ctx.score[train[chosen], target]), chosen != sbs


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
    classes = strata(ctx, problems)
    classes.round(4).to_csv(at.DATA_DIR / "strata.csv")

    rows = []
    for split, unit, targets, train in at.splits(problems, group, family):
        train_index = np.array([index[p] for p in train])
        for target in targets:
            t = index[target]
            for row in np.flatnonzero(ctx.sample_problem == t):
                base = at.recommend(ctx, t, row, train_index)
                entry = {
                    "split": split,
                    "unit": unit,
                    "target": target,
                    "group": group[target],
                    "stratum": classes.loc[target, "stratum"],
                    **{
                        m: base[m]
                        for m in (
                            "random",
                            "default",
                            "metadata_1nn",
                            "landscape_1nn",
                            "knn_selector",
                            "sbs",
                            "oracle",
                        )
                    },
                }
                for k, delta in GRID:
                    value, deviated = consensus(ctx, t, row, train_index, k, delta)
                    entry[f"consensus_k{k}_d{delta}"] = value
                    entry[f"deviates_k{k}_d{delta}"] = deviated
                rows.append(entry)
    long = pd.DataFrame(rows)
    long.to_csv(at.DATA_DIR / "consensus_long.csv", index=False)

    methods = (
        ["random", "default", "metadata_1nn", "landscape_1nn", "knn_selector"]
        + [f"consensus_k{k}_d{d}" for k, d in GRID]
        + ["sbs", "oracle"]
    )
    result = {
        "note": "Exploratory, not pre-registered; strata are defined from the matrix itself.",
        "strata_counts": classes.stratum.value_counts().to_dict(),
        "by_split": {},
        "by_stratum_logo": {},
    }
    for split in ("LOGO", "LOFO", "random"):
        x = long[long.split == split]
        per_target = x.groupby(["unit", "target", "group"])[methods].mean().reset_index()
        loss = x[methods].rsub(x["oracle"], axis=0)
        logo_groups = per_target.groupby("group")[methods].mean()
        summary = {}
        for m in methods:
            entry = {
                "mean_hvn": round(float(per_target[m].mean()), 4),
                "median_loss": round(float(loss[m].median()), 4),
                "share_loss_above_0.10": round(float((loss[m] > 0.10).mean()), 3),
                "cvar90": round(float(np.sort(loss[m])[-max(1, len(loss) // 10) :].mean()), 4),
            }
            if split == "LOGO" and m not in ("sbs", "oracle"):
                diff = logo_groups[m] - logo_groups["sbs"]
                entry["vs_sbs_groups_mean"] = round(float(diff.mean()), 4)
                entry["vs_sbs_groups_w_l_t"] = [
                    int((diff > TIE).sum()),
                    int((diff < -TIE).sum()),
                    int((diff.abs() <= TIE).sum()),
                ]
                entry["vs_sbs_p_greater"] = (
                    round(
                        float(
                            wilcoxon(
                                logo_groups[m], logo_groups["sbs"], alternative="greater"
                            ).pvalue
                        ),
                        4,
                    )
                    if (diff.abs() > TIE).any()
                    else 1.0
                )
            summary[m] = entry
        for k, d in GRID:
            summary[f"consensus_k{k}_d{d}"]["share_deviating_from_sbs"] = round(
                float(x[f"deviates_k{k}_d{d}"].mean()), 3
            )
        result["by_split"][split] = summary
    x = long[long.split == "LOGO"]
    for stratum, g in x.groupby("stratum"):
        per_target = g.groupby("target")[methods].mean()
        result["by_stratum_logo"][stratum] = {
            "targets": int(len(per_target)),
            **{m: round(float(per_target[m].mean()), 4) for m in methods},
        }
    (at.DATA_DIR / "consensus_strata.json").write_text(json.dumps(result, indent=2) + "\n")
    show = pd.DataFrame(
        {
            s: {m: v["mean_hvn"] for m, v in result["by_split"][s].items()}
            for s in result["by_split"]
        }
    )
    print(show.to_string())
    print(pd.DataFrame(result["by_stratum_logo"]).to_string())
    print(
        json.dumps(
            {
                m: {k: v for k, v in e.items() if k != "mean_hvn"}
                for m, e in result["by_split"]["LOGO"].items()
            },
            indent=1,
        )
    )


if __name__ == "__main__":
    main()
