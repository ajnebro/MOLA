"""Phase 4 replication on bbob-biobj (phase 3c, amendment 3): G7's two conditions per split.

Same policy as analyze_g7_phase3.py (policy.py, alpha = 0.05), on phase 3c's splits
(analyze_3c.splits) and recommendations (analyze_3c.recommend, unchanged). The fallback is the
irace generalist of the split: gen__all in S1; gen__g<g> in S2; in S3, gen__g<g> with g the
smallest bbob group among the target function's components (gen__all saw the left-out function;
gen__g<g> did not, and it is trained on a subset of S3's training set).

Reported per split, over the 55 functions (function value = mean over its targets and samples):
  1. non-inferiority: one-sided Wilcoxon of (pi_0.05 - generalist + 0.005) > 0, p < 0.05;
  2. tail: share of target samples with loss > 0.10 against the oracle donor under pi_0.05 at most
     half the share under knn_selector;
plus the coverage-risk table for alpha in policy.ALPHAS and the coverage by split. This is a
pre-registered secondary analysis of phase 3c: it does not enter the Holm correction of G4 and G5.

Run locally after analyze_3c.py:  python research/phase4/scripts/analyze_g7_3c.py
Reads MOLA_PHASE3C_HVN (default phase3c/data/hvn.csv); writes data/g7_3c_long.csv and
data/g7_3c.json (MOLA_PHASE4_OUT overrides the directory).
"""

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase3c" / "scripts"))

import analyze_3c as a3c  # noqa: E402
from policy import ALPHA, ALPHAS, distance_and_s1  # noqa: E402

OUT = Path(os.environ.get("MOLA_PHASE4_OUT", HERE.parent / "data"))
HVN = Path(os.environ.get("MOLA_PHASE3C_HVN", a3c.DATA / "hvn.csv"))
MARGIN, TAIL, TIE = 0.005, 0.10, 1e-9


def fallback(split, generalist, catalogue, target):
    if split == "S3":
        return f"gen__g{min(catalogue[target]['groups'])}"
    return generalist


def main() -> None:
    catalogue = json.loads((a3c.DATA / "catalogue.json").read_text())
    samples = pd.read_csv(a3c.DATA / "features_sample_scaled.csv")
    data = a3c.Data(catalogue, samples, pd.read_csv(HVN))

    rows = []
    for split, unit, target, train, generalist in a3c.splits(data):
        train = np.array(train)
        gen = fallback(split, generalist, catalogue, target)
        gen_value = float(data.H.loc[gen, target])
        for row in np.flatnonzero(data.sample_problem == target):
            base = a3c.recommend(data, target, row, list(train), generalist)
            policy = distance_and_s1(data.values, data.sample_problem, train, row)
            entry = {
                "split": split,
                "unit": unit,
                "target": target,
                "function": catalogue[target]["function"],
                "generalist_config": gen,
                "generalist": gen_value,
                "knn_selector": base["knn_selector"],
                "landscape_1nn": base["landscape_1nn"],
                "oracle": base["oracle"],
                "d_units": policy["d_units"],
                "s1": policy["s1"],
            }
            for a in ALPHAS:
                transfer = policy["s1"] >= a
                entry[f"pi_{a}"] = base["knn_selector"] if transfer else gen_value
                entry[f"transfers_{a}"] = bool(transfer)
            rows.append(entry)
    long = pd.DataFrame(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    long.to_csv(OUT / "g7_3c_long.csv", index=False)

    main_pi = f"pi_{ALPHA}"
    result = {}
    for split, x in long.groupby("split"):
        functions = x.groupby("function")[[main_pi, "generalist"]].mean()
        shifted = functions[main_pi] - functions["generalist"] + MARGIN
        p = (
            float(wilcoxon(shifted, alternative="greater").pvalue)
            if (shifted.abs() > TIE).any()
            else 1.0
        )
        tail_pi = float((x["oracle"] - x[main_pi] > TAIL).mean())
        tail_knn = float((x["oracle"] - x["knn_selector"] > TAIL).mean())
        result[split] = {
            "functions": int(len(functions)),
            "mean_difference": round(
                float((functions[main_pi] - functions["generalist"]).mean()), 4
            ),
            "p_noninferiority": p,
            "tail_share_pi": round(tail_pi, 4),
            "tail_share_knn_selector": round(tail_knn, 4),
            "condition_1": bool(p < 0.05),
            "condition_2": bool(tail_pi <= 0.5 * tail_knn),
            "coverage_risk": {
                str(a): {
                    "coverage": round(float(x[f"transfers_{a}"].mean()), 3),
                    "mean_hvn": round(float(x.groupby("function")[f"pi_{a}"].mean().mean()), 4),
                    "share_loss_gt_0.10": round(
                        float((x["oracle"] - x[f"pi_{a}"] > TAIL).mean()), 3
                    ),
                }
                for a in ALPHAS
            },
            "median_d_units": round(float(x["d_units"].median()), 3),
        }
    (OUT / "g7_3c.json").write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {s: {k: v for k, v in r.items() if k != "coverage_risk"} for s, r in result.items()},
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
