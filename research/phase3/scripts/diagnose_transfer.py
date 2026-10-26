"""Phase 3, post hoc diagnosis (not pre-registered): why is the random donor so good and the landscape so weak?

1. Spread of the 36 candidate configurations on each target: worst, median, mean (= the random
   donor), best (= the oracle donor), and how many donors are within 0.01 of the best.
2. Does feature distance predict transfer quality? Per target, the Spearman correlation between the
   distance to each other problem and the HVn of that problem's c*_P on the target; negative means
   that closer donors are better. Landscape (robust-scaled 49 features) and metadata distances.
3. Typical versus tail loss against the oracle donor, per method and split, over target samples:
   median, mean, share of losses above 0.10, and the mean of the worst 10 % (CVaR 90 %).

Run locally:  MOLA_PHASE3_MATRIX=... python research/phase3/scripts/diagnose_transfer.py
Writes data/diagnosis.json and data/donor_spread.csv.
"""

import json

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import analyze_transfer as at

METHODS = ["random", "metadata_1nn", "landscape_1nn", "knn_selector", "sbs", "default"]


def _robust(values):
    med = np.nanmedian(values, axis=0)
    q75, q25 = np.nanpercentile(values, [75, 25], axis=0)
    iqr = q75 - q25
    keep = np.isfinite(med) & (iqr > 0) & np.isfinite(values).all(axis=0)
    return (values[:, keep] - med[keep]) / iqr[keep]


def main() -> None:
    problems = at.pilot_problems()
    _, family = at.groups_and_families(problems)
    ctx = at.Context(problems, pd.read_csv(at.PRIMARY_FEATURES), pd.read_csv(at.RAW_OBJECTIVE_FEATURES),
                     at.metadata(problems), at.hvn_matrix(problems))
    score = ctx.score  # score[a, b]: mean HVn of c*_a on problem b

    spread, corr = [], []
    z = _robust(ctx.means)
    meta = (ctx.meta - ctx.meta.mean(0)) / np.where(ctx.meta.std(0) > 0, ctx.meta.std(0), 1.0)
    for j, q in enumerate(problems):
        others = [i for i in range(len(problems)) if i != j]
        v = score[others, j]
        spread.append({"target": q, "family": family[q], "worst": v.min(), "median": np.median(v),
                       "random_mean": v.mean(), "oracle_best": v.max(), "own": score[j, j],
                       "donors_within_0.01_of_best": int((v >= v.max() - 0.01).sum())})
        corr.append({"target": q,
                     "rho_landscape": spearmanr(np.linalg.norm(z[others] - z[j], axis=1), v)[0],
                     "rho_metadata": spearmanr(np.linalg.norm(meta[others] - meta[j], axis=1), v)[0]})
    spread = pd.DataFrame(spread).merge(pd.DataFrame(corr), on="target").sort_values("oracle_best")
    spread.round(4).to_csv(at.DATA_DIR / "donor_spread.csv", index=False)

    long = pd.read_csv(at.DATA_DIR / "transfer_long.csv")
    losses = {}
    for split in ("LOGO", "LOFO"):
        rows = long[long.split == split]
        loss = rows[METHODS].rsub(rows["oracle"], axis=0)
        worst = max(1, len(loss) // 10)
        losses[split] = {
            "median": loss.median().round(4).to_dict(), "mean": loss.mean().round(4).to_dict(),
            "share_above_0.10": (loss > 0.10).mean().round(3).to_dict(),
            "cvar90": {m: round(float(np.sort(loss[m])[-worst:].mean()), 4) for m in METHODS}}
    result = {
        "note": "Post hoc, not pre-registered.",
        "targets_with_median_donor_within_0.01_of_best": int((spread.oracle_best - spread["median"] < 0.01).sum()),
        "spearman_distance_vs_donor_hvn_mean_over_targets": spread[["rho_landscape", "rho_metadata"]].mean().round(3).to_dict(),
        "loss_against_oracle_over_target_samples": losses,
    }
    (at.DATA_DIR / "diagnosis.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
