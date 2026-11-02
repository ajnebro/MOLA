"""Phase 4 pre-registered analysis on phase 3 + 3g: gate G7 (preregistration.md, section 4).

For every split of phase 3 (LOGO, LOFO, random 80/20 by problem; analyze_transfer.splits) and every
target sample: the methods of analyze_transfer.recommend (unchanged), the irace generalist of the
split, d and s1 of policy.py, the policy pi_alpha for alpha in policy.ALPHAS, and the loss-calibrated
variant pi_eps (epsilon in {0.01, 0.02}, beta = 0.10).

Generalist (D11, D12): under LOGO, gen__logo_NN of the target's formulation group (its training set
equals the split's); under LOFO, gen__lofo_<family>; under the random split, gen__lofo_<family>
(a subset of the split's training set: descriptive only).

Gate G7 (LOGO, the 32 formulation groups; group value = mean over its targets and samples):
  1. non-inferiority: one-sided Wilcoxon signed-rank of (pi_0.05 - generalist + 0.005) > 0, p < 0.05;
  2. tail: the share of target samples whose loss against the oracle donor exceeds 0.10 is, under
     pi_0.05, at most half the share under knn_selector.
G7 passes when both hold.

Run locally:
    MOLA_PHASE3_MATRIX=... MOLA_PHASE3G_RAW=... python research/phase4/scripts/analyze_g7_phase3.py
Writes data/g7_phase3_long.csv and data/g7_phase3.json (MOLA_PHASE4_OUT overrides the directory).
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase3" / "scripts"))
sys.path.insert(0, str(HERE.parents[1] / "phase3g" / "scripts"))

import analyze_3g as a3g  # noqa: E402
import analyze_transfer as at  # noqa: E402
from policy import (  # noqa: E402
    ALPHA,
    ALPHAS,
    distance_and_s1,
    loss_calibrated_threshold,
    noise,
    scaled,
)

OUT = Path(os.environ.get("MOLA_PHASE4_OUT", HERE.parent / "data"))
TASKS = json.loads((HERE.parents[1] / "phase3g" / "data" / "generalist_tasks.json").read_text())
MARGIN, TAIL, EPSILONS, TIE = 0.005, 0.10, (0.01, 0.02), 1e-9


def generalist_for(split, group, family):
    if split == "LOGO":
        task = next(k for k, v in TASKS.items() if v["left_out_group"] == group)
        return f"gen__{task[len('gen_') :]}"
    return a3g.generalist_of(family)


def pseudo_targets(ctx, train, oracle_of):
    """(d_units, 1-NN loss) for every sample of every training problem against the other ones."""
    pairs = []
    for i, p in enumerate(train):
        others = np.delete(train, i)
        for row in np.flatnonzero(ctx.sample_problem == p):
            samples, owner, means, query = scaled(
                ctx.sample_values, ctx.sample_problem, others, row
            )
            distance = np.linalg.norm(means - query, axis=1)
            _, unit = noise(samples, owner)
            nearest = others[int(np.argmin(distance))]
            pairs.append((distance.min() / unit, oracle_of(p, others) - ctx.score[nearest, p]))
    return pairs


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
    configs = sorted({generalist_for("LOFO", None, f) for f in family.values()}) + [
        f"gen__{k[len('gen_') :]}" for k in TASKS if k.startswith("gen_logo")
    ]
    table = a3g.generalists_hvn(problems, configs).pivot(
        index="config", columns="problem", values="hvn"
    )

    def oracle_of(p, donors):
        return ctx.score[donors, p].max()

    rows = []
    for split, unit, targets, train in at.splits(problems, group, family):
        train_index = np.array([index[p] for p in train])
        thresholds = {}
        if split != "random":  # the loss-calibrated variant is computed on LOGO and LOFO only
            pseudo = pseudo_targets(ctx, train_index, oracle_of)
            thresholds = {e: loss_calibrated_threshold(pseudo, e) for e in EPSILONS}
        for target in targets:
            t = index[target]
            generalist = generalist_for(split, group[target], family[target])
            gen_value = float(table.loc[generalist, target])
            for row in np.flatnonzero(ctx.sample_problem == t):
                base = at.recommend(ctx, t, row, train_index)
                policy = distance_and_s1(ctx.sample_values, ctx.sample_problem, train_index, row)
                entry = {
                    "split": split,
                    "unit": unit,
                    "target": target,
                    "group": group[target],
                    "family": family[target],
                    "generalist_config": generalist,
                    "generalist": gen_value,
                    **{
                        m: base[m]
                        for m in ("knn_selector", "landscape_1nn", "random", "default", "sbs")
                    },
                    "oracle": base["oracle"],
                    "d_units": policy["d_units"],
                    "s1": policy["s1"],
                    "nearest_donor": problems[train_index[policy["nearest"]]],
                }
                for a in ALPHAS:
                    transfer = policy["s1"] >= a
                    entry[f"pi_{a}"] = base["knn_selector"] if transfer else gen_value
                    entry[f"transfers_{a}"] = bool(transfer)
                for e, threshold in thresholds.items():
                    transfer = policy["d_units"] <= threshold
                    entry[f"pi_eps_{e}"] = base["knn_selector"] if transfer else gen_value
                    entry[f"t_eps_{e}"] = threshold
                rows.append(entry)
    long = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    long.to_csv(OUT / "g7_phase3_long.csv", index=False)

    main_pi = f"pi_{ALPHA}"
    logo = long[long.split == "LOGO"]
    groups = (
        logo.groupby(["unit", "target"])[[main_pi, "generalist"]].mean().groupby(level=0).mean()
    )
    shifted = groups[main_pi] - groups["generalist"] + MARGIN
    p = (
        float(wilcoxon(shifted, alternative="greater").pvalue)
        if (shifted.abs() > TIE).any()
        else 1.0
    )
    tail_pi = float((logo["oracle"] - logo[main_pi] > TAIL).mean())
    tail_knn = float((logo["oracle"] - logo["knn_selector"] > TAIL).mean())
    gate = {
        "rule": "LOGO: (1) one-sided Wilcoxon of pi_0.05 - generalist + 0.005 > 0 over the 32 "
        "groups, p < 0.05; (2) share of loss > 0.10 under pi_0.05 <= half the share under "
        "knn_selector",
        "groups": int(len(groups)),
        "mean_difference": round(float((groups[main_pi] - groups["generalist"]).mean()), 4),
        "p_noninferiority": p,
        "tail_share_pi": round(tail_pi, 4),
        "tail_share_knn_selector": round(tail_knn, 4),
        "condition_1": bool(p < 0.05),
        "condition_2": bool(tail_pi <= 0.5 * tail_knn),
    }
    gate["passes"] = gate["condition_1"] and gate["condition_2"]

    strata = pd.read_csv(at.DATA_DIR / "strata.csv").set_index("target")["stratum"]
    secondary = {}
    for split, x in long.groupby("split"):
        loss = lambda m, x=x: x["oracle"] - x[m]  # noqa: E731
        entry = {
            "mean_hvn": {
                m: round(float(x.groupby("target")[m].mean().mean()), 4)
                for m in ["generalist", "knn_selector", "sbs", "default", "oracle"]
                + [f"pi_{a}" for a in ALPHAS]
                + [c for c in x.columns if c.startswith("pi_eps_")]
            },
            "coverage_risk": {
                str(a): {
                    "coverage": round(float(x[f"transfers_{a}"].mean()), 3),
                    "share_loss_gt_0.10": round(float((loss(f"pi_{a}") > TAIL).mean()), 3),
                    "transfer_branch_minus_generalist": round(
                        float((x["knn_selector"] - x["generalist"])[x[f"transfers_{a}"]].mean()),
                        4,
                    )
                    if x[f"transfers_{a}"].any()
                    else None,
                }
                for a in ALPHAS
            },
            "coverage_by_stratum": {
                s: round(float(y[f"transfers_{ALPHA}"].mean()), 3)
                for s, y in x.groupby(x["target"].map(strata))
            },
            "high_s1_large_loss": x[(x["s1"] >= ALPHA) & (loss("knn_selector") > TAIL)][
                ["target", "nearest_donor", "d_units", "s1"]
            ]
            .drop_duplicates(["target", "nearest_donor"])
            .round(3)
            .to_dict("records"),
        }
        for e in EPSILONS:
            column = f"t_eps_{e}"
            if column in x:
                entry[f"threshold_eps_{e}_units"] = {
                    "median": round(float(x[column].median()), 3),
                    "min": round(float(x[column].min()), 3),
                    "max": round(float(x[column].max()), 3),
                }
        secondary[split] = entry
    result = {"gate_g7": gate, "secondary": secondary}
    (OUT / "g7_phase3.json").write_text(json.dumps(result, indent=2, default=str) + "\n")
    print(json.dumps(gate, indent=2))


if __name__ == "__main__":
    main()
