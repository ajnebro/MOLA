"""Phase 3, exploratory: transfer loss against landscape distance over all ordered problem pairs.

Makes traceable two analyses first computed ad hoc on 2026-10-31 and cited in
research/review/briefing_2026-10-31.md and in pending question 20 (the external review of
2026-11-01 found they were not in the repository):

1. Distance against loss over the 37 x 36 = 1 332 ordered pairs (donor P -> target Q).
   - Features: the 49 MOLA features (`sample` scaling), robust-scaled over the 185 samples (median,
     IQR; descriptive, no split), problem means over the 5 LHS samples.
   - Distance: Euclidean between problem means, in noise units. Two noise references are reported:
     `pair`, the median distance between two samples of the same problem; and `loso`, the distance
     from one sample to the mean of the other four, which is the statistic a recommender applies
     (one target sample against a donor's mean).
   - Loss: HVn of the best donor on Q minus HVn of c*_P on Q (`loss_oracle`), and HVn of c*_Q on Q
     minus HVn of c*_P on Q (`loss_self`).
2. The LOGO comparisons of D11 over the 32 formulation groups (one-sided Wilcoxon, uncorrected):
   landscape_1nn and knn_selector against the random tuned donor, default NSGA-II and metadata_1nn,
   from data/transfer_long.csv.

Run locally:  MOLA_PHASE3_MATRIX=... python research/phase3/scripts/distance_vs_loss.py
Writes data/distance_vs_loss_pairs.csv and data/distance_vs_loss.json.
"""

import itertools
import json

import analyze_transfer as at
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon

BINS = [0, 1.5, 3, 6, np.inf]


def summarize(x: pd.DataFrame) -> dict:
    return {
        "pairs": int(len(x)),
        "loss_le_0.01": round(float((x.loss_oracle <= 0.01).mean()), 3),
        "loss_gt_0.10": round(float((x.loss_oracle > 0.10).mean()), 3),
        "median_loss": round(float(x.loss_oracle.median()), 4),
        "same_family": round(float(x.same_family.mean()), 3),
        "easy_target": round(float(x.easy_target.mean()), 3),
    }


def main() -> None:
    problems = at.pilot_problems()
    _, family = at.groups_and_families(problems)
    samples = pd.read_csv(at.PRIMARY_FEATURES)
    ctx = at.Context(
        problems,
        samples,
        pd.read_csv(at.RAW_OBJECTIVE_FEATURES),
        at.metadata(problems),
        at.hvn_matrix(problems),
    )
    stratum = pd.read_csv(at.DATA_DIR / "strata.csv").set_index("target")["stratum"]
    n = len(problems)

    values = ctx.sample_values
    defined = np.isfinite(values).all(axis=0)
    q75, median, q25 = np.percentile(values[:, defined], [75, 50, 25], axis=0)
    iqr = q75 - q25
    keep = np.flatnonzero(defined)[iqr > 0]
    z = (values[:, keep] - median[iqr > 0]) / iqr[iqr > 0]
    owner = ctx.sample_problem
    means = np.vstack([z[owner == i].mean(axis=0) for i in range(n)])

    pair, loso = [], []
    for i in range(n):
        own = z[owner == i]
        pair += [np.linalg.norm(a - b) for a, b in itertools.combinations(own, 2)]
        loso += [
            np.linalg.norm(own[j] - np.delete(own, j, axis=0).mean(axis=0)) for j in range(len(own))
        ]
    pair, loso = np.array(pair), np.array(loso)
    unit = float(np.median(pair))

    score = ctx.score  # score[a, b]: HVn of c*_a on problem b
    rows = []
    for q in range(n):
        donors = [p for p in range(n) if p != q]
        oracle = max(score[p, q] for p in donors)
        for p in donors:
            rows.append(
                {
                    "donor": problems[p],
                    "target": problems[q],
                    "distance_units": float(np.linalg.norm(means[p] - means[q]) / unit),
                    "loss_oracle": float(oracle - score[p, q]),
                    "loss_self": float(score[q, q] - score[p, q]),
                    "same_family": family[problems[p]] == family[problems[q]],
                    "easy_target": stratum[problems[q]] == "easy",
                }
            )
    pairs = pd.DataFrame(rows)
    pairs.round(5).to_csv(at.DATA_DIR / "distance_vs_loss_pairs.csv", index=False)
    pairs["bin"] = pd.cut(pairs.distance_units, BINS).astype(str)

    def by_bin(x):
        return {b: summarize(y) for b, y in x.groupby("bin", sort=False)}

    other = pairs[~pairs.same_family]
    result = {
        "note": "Exploratory, descriptive. Distances in units of the median same-problem "
        "sample-pair distance.",
        "noise": {
            "unit": round(unit, 4),
            "pair_p95_units": round(float(np.percentile(pair, 95) / unit), 3),
            "loso_p95_units": round(float(np.percentile(loso, 95) / unit), 3),
        },
        "all_pairs": by_bin(pairs),
        "non_easy_targets": by_bin(pairs[~pairs.easy_target]),
        "different_family": by_bin(other),
        "spearman_distance_loss": {
            "all": round(float(spearmanr(pairs.distance_units, pairs.loss_oracle)[0]), 3),
            "different_family": round(
                float(spearmanr(other.distance_units, other.loss_oracle)[0]), 3
            ),
        },
    }

    long = pd.read_csv(at.DATA_DIR / "transfer_long.csv")
    methods = ["landscape_1nn", "knn_selector", "random", "default", "metadata_1nn"]
    groups = long[long.split == "LOGO"].groupby("unit")[methods].mean()
    comparisons = {}
    for m in ("landscape_1nn", "knn_selector"):
        for b in ("random", "default", "metadata_1nn"):
            d = groups[m] - groups[b]
            comparisons[f"{m}_vs_{b}"] = {
                "mean": round(float(d.mean()), 4),
                "wins_losses_ties": [
                    int((d > 1e-9).sum()),
                    int((d < -1e-9).sum()),
                    int((d.abs() <= 1e-9).sum()),
                ],
                "p_greater": float(wilcoxon(groups[m], groups[b], alternative="greater").pvalue),
            }
    result["logo_d11_comparisons_uncorrected"] = comparisons
    (at.DATA_DIR / "distance_vs_loss.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
