"""Phase 3, exploratory (not pre-registered; requested by the user on 2026-10-26): one column per
distance for the nearest-neighbour recommender, on the existing performance matrix.

Columns: random donor, default NSGA-II, metadata_1nn and the landscape nearest neighbour under each
distance, then the SBS and the oracle donor. Existing ones come from analyze_transfer.recommend:
- euclidean: the pre-registered landscape_1nn;
- thesis: thesis_1nn;
- learned: loss_predictor.

New ones, all on the same 49 sample-scaled features with the same undefined/constant filtering:
- l1: Manhattan distance on the robust-scaled features (median, IQR over T's samples);
- pca_whitened: PCA on T's robust-scaled samples, keeping the components that explain 95 % of the
  variance, each divided by its standard deviation, then Euclidean. A Mahalanobis distance
  restricted to the main components, so that redundant features do not count several times;
- rank: each feature replaced by its empirical percentile among T's samples (ties count half), then
  Euclidean. Insensitive to scale and to extreme values.

Every column picks one donor per (target, sample), as landscape_1nn does, and reads its HVn from the
matrix. Splits and aggregation follow analyze_transfer.py. Exploratory: the G3 verdict does not
change, and a distance chosen here would need its own pre-registration and the reserved problems.

Run locally:  MOLA_PHASE3_MATRIX=... python research/phase3/scripts/distance_table.py
Writes data/distance_table.csv, data/distance_table_long.csv and data/distance_table.json.
"""

import json

import analyze_transfer as at
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon

PCA_VARIANCE = 0.95
COLUMNS = [
    "random",
    "default",
    "metadata_1nn",
    "euclidean",
    "thesis",
    "learned",
    "l1",
    "pca_whitened",
    "rank",
    "sbs",
    "oracle",
]
LANDSCAPE = ["euclidean", "thesis", "learned", "l1", "pca_whitened", "rank"]
TIE = 1e-9


def _scaled(ctx, query, train):
    """T's samples, T's problem means and the query, robust-scaled on usable features."""
    rows = ctx.sample_values[np.isin(ctx.sample_problem, train)]
    defined = np.isfinite(rows).all(axis=0) & np.isfinite(query)
    q75, median, q25 = np.percentile(rows[:, defined], [75, 50, 25], axis=0)
    iqr = q75 - q25
    keep = np.flatnonzero(defined)[iqr > 0]
    median, iqr = median[iqr > 0], iqr[iqr > 0]
    return (
        (rows[:, keep] - median) / iqr,
        (ctx.means[train][:, keep] - median) / iqr,
        (query[keep] - median) / iqr,
    )


def _pca_whitened(samples, means, query):
    center = samples.mean(axis=0)
    _, singular, vt = np.linalg.svd(samples - center, full_matrices=False)
    variance = singular**2 / (len(samples) - 1)
    k = int(np.searchsorted(np.cumsum(variance) / variance.sum(), PCA_VARIANCE) + 1)
    scale = np.sqrt(variance[:k])
    return ((means - center) @ vt[:k].T) / scale, ((query - center) @ vt[:k].T) / scale


def _percentiles(samples, values):
    ordered = np.sort(samples, axis=0)
    n = len(samples)
    out = np.empty_like(values, dtype=float)
    for f in range(samples.shape[1]):
        below = np.searchsorted(ordered[:, f], values[..., f], side="left")
        at_or_below = np.searchsorted(ordered[:, f], values[..., f], side="right")
        out[..., f] = (below + 0.5 * (at_or_below - below)) / n
    return out


def new_distances(ctx, row, train):
    """Distance from the query sample to every training problem, for the three new distances."""
    samples, means, query = _scaled(ctx, ctx.sample_values[row], train)
    whitened_means, whitened_query = _pca_whitened(samples, means, query)
    ranks_means, ranks_query = (
        _percentiles(samples, means),
        _percentiles(samples, query[None, :])[0],
    )
    return {
        "l1": np.abs(means - query).sum(axis=1),
        "pca_whitened": np.linalg.norm(whitened_means - whitened_query, axis=1),
        "rank": np.linalg.norm(ranks_means - ranks_query, axis=1),
        "euclidean": np.linalg.norm(means - query, axis=1),
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

    rows = []
    for split, unit, targets, train in at.splits(problems, group, family):
        train_index = np.array([index[p] for p in train])
        for target in targets:
            t = index[target]
            on_target = ctx.score[train_index, t]
            for row in np.flatnonzero(ctx.sample_problem == t):
                base = at.recommend(ctx, t, row, train_index)
                distances = new_distances(ctx, row, train_index)
                assert np.isclose(
                    on_target[np.argmin(distances["euclidean"])], base["landscape_1nn"]
                )
                rows.append(
                    {
                        "split": split,
                        "unit": unit,
                        "target": target,
                        "group": group[target],
                        "sample": int(samples.loc[row, "seed"]),
                        "random": base["random"],
                        "default": base["default"],
                        "metadata_1nn": base["metadata_1nn"],
                        "euclidean": base["landscape_1nn"],
                        "thesis": base["thesis_1nn"],
                        "learned": base["loss_predictor"],
                        **{
                            name: on_target[np.argmin(distances[name])]
                            for name in ("l1", "pca_whitened", "rank")
                        },
                        "sbs": base["sbs"],
                        "oracle": base["oracle"],
                    }
                )
    long = pd.DataFrame(rows)
    long.to_csv(at.DATA_DIR / "distance_table_long.csv", index=False)

    per_target = long.groupby(["split", "unit", "target", "group"])[COLUMNS].mean().reset_index()
    table = per_target.groupby("split")[COLUMNS].mean().T[["LOGO", "LOFO", "random"]]
    table.round(4).to_csv(at.DATA_DIR / "distance_table.csv")

    logo = per_target[per_target.split == "LOGO"].groupby("group")[COLUMNS].mean()

    def one_sided(a, b):
        difference = logo[a] - logo[b]
        p = (
            float(wilcoxon(logo[a], logo[b], alternative="greater").pvalue)
            if (difference.abs() > TIE).any()
            else 1.0
        )
        return {
            "mean": round(float(difference.mean()), 4),
            "wins_losses_ties": [
                int((difference > TIE).sum()),
                int((difference < -TIE).sum()),
                int((difference.abs() <= TIE).sum()),
            ],
            "p_greater": round(p, 4),
        }

    logo_rows = long[long.split == "LOGO"]
    loss = logo_rows[COLUMNS].rsub(logo_rows["oracle"], axis=0)
    result = {
        "note": "Exploratory, not pre-registered; p-values uncorrected. G3 is unchanged.",
        "pca_variance_kept": PCA_VARIANCE,
        "logo_vs_metadata_1nn": {d: one_sided(d, "metadata_1nn") for d in LANDSCAPE},
        "logo_vs_sbs": {d: one_sided(d, "sbs") for d in LANDSCAPE},
        "logo_loss_vs_oracle_median": loss.median().round(4).to_dict(),
        "logo_loss_vs_oracle_share_above_0.10": (loss > 0.10).mean().round(3).to_dict(),
    }
    # Signal of each distance: Spearman between distance and donor quality, all other problems as donors.
    signal = {name: [] for name in ("euclidean", "l1", "pca_whitened", "rank")}
    for target in problems:
        t = index[target]
        others = np.array([i for i in range(len(problems)) if i != t])
        quality = ctx.score[others, t]
        for row in np.flatnonzero(ctx.sample_problem == t):
            for name, distance in new_distances(ctx, row, others).items():
                signal[name].append(spearmanr(distance, quality)[0])
    result["spearman_distance_vs_donor_hvn"] = {
        k: round(float(np.nanmean(v)), 3) for k, v in signal.items()
    }
    (at.DATA_DIR / "distance_table.json").write_text(json.dumps(result, indent=2) + "\n")
    print(table.round(3).to_string())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
