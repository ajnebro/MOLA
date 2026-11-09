"""Phase 3c, pre-registered secondary analyses (preregistration.md section 6) not in analyze_3c.py.

All descriptive; none changes G4 or G5.
- Loss against the oracle donor: the mean of the worst 10 % of target samples, per split and method
  (analyze_3c.py reports the median and the share above 0.10).
- Ceiling of perfect similarity (S1): same_function against the generalist and against the SBS, over
  the 55 functions.
- Alternative distances for the landscape nearest neighbour (exploratory): L1, PCA-whitened and
  rank, as in phase3/scripts/distance_table.py, and Euclidean on the features computed with unscaled
  objectives (data/features_raw_objectives.csv).
- Budgets of 5 000 and 10 000 evaluations: analyze_3c.py's whole pipeline with HVn at that budget,
  normalised by the union of the matrix fronts at that budget. The configurations were tuned for
  20 000.
- Seed noise: the standard error over the 10 seeds of each matrix cell's HVn at 20 000, to read the
  size of the differences.

Run locally after analyze_3c.py:
    MOLA_PHASE3C_MATRIX=... python research/phase3c/scripts/secondary_3c.py
Writes data/secondary.json.
"""

import json

import analyze_3c as a3c
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

PCA_VARIANCE = 0.95
DISTANCES = ["euclidean", "l1", "pca_whitened", "rank", "raw_objectives"]


def _pca_whitened(samples, means, query):
    """As in phase3/scripts/distance_table.py."""
    center = samples.mean(axis=0)
    _, singular, vt = np.linalg.svd(samples - center, full_matrices=False)
    variance = singular**2 / (len(samples) - 1)
    k = int(np.searchsorted(np.cumsum(variance) / variance.sum(), PCA_VARIANCE) + 1)
    scale = np.sqrt(variance[:k])
    return ((means - center) @ vt[:k].T) / scale, ((query - center) @ vt[:k].T) / scale


def _percentiles(samples, values):
    """As in phase3/scripts/distance_table.py: empirical percentile, ties count half."""
    ordered = np.sort(samples, axis=0)
    out = np.empty_like(values, dtype=float)
    for f in range(samples.shape[1]):
        below = np.searchsorted(ordered[:, f], values[..., f], side="left")
        at_or_below = np.searchsorted(ordered[:, f], values[..., f], side="right")
        out[..., f] = (below + 0.5 * (at_or_below - below)) / len(samples)
    return out


def _scaled(data, train, query):
    """T's samples, T's problem means and the query, robust-scaled as in analyze_3c._robust_z."""
    rows = data.values[np.isin(data.sample_problem, train)]
    defined = np.isfinite(rows).all(axis=0) & np.isfinite(query)
    q75, median, q25 = np.percentile(rows[:, defined], [75, 50, 25], axis=0)
    iqr = q75 - q25
    keep = np.flatnonzero(defined)[iqr > 0]
    median, iqr = median[iqr > 0], iqr[iqr > 0]
    means = np.vstack([data.means[p] for p in train])
    return (
        (rows[:, keep] - median) / iqr,
        (means[:, keep] - median) / iqr,
        (query[keep] - median) / iqr,
    )


def distance_picks(data, raw, row, train):
    """HVn on the target of the landscape nearest neighbour under each distance."""
    samples, means, query = _scaled(data, train, data.values[row])
    whitened_means, whitened_query = _pca_whitened(samples, means, query)
    distances = {
        "euclidean": np.linalg.norm(means - query, axis=1),
        "l1": np.abs(means - query).sum(axis=1),
        "pca_whitened": np.linalg.norm(whitened_means - whitened_query, axis=1),
        "rank": np.linalg.norm(
            _percentiles(samples, means) - _percentiles(samples, query[None, :])[0], axis=1
        ),
    }
    raw_row = np.flatnonzero(
        (raw.sample_problem == data.sample_problem[row])
        & (raw.samples.seed.to_numpy() == data.samples.loc[row, "seed"])
    )[0]
    _, raw_means, raw_query = _scaled(raw, train, raw.values[raw_row])
    distances["raw_objectives"] = np.linalg.norm(raw_means - raw_query, axis=1)
    configs = [data.config_of(p) for p in train]
    target = data.sample_problem[row]
    on_target = data.H.loc[configs, target].to_numpy()
    return {name: float(on_target[int(np.argmin(d))]) for name, d in distances.items()}


def run_pipeline(data):
    """analyze_3c.main's recommendation loop, returning the long table."""
    rows = []
    for split, unit, target, train, generalist in a3c.splits(data):
        for row in np.flatnonzero(data.sample_problem == target):
            rows.append(
                {
                    "split": split,
                    "unit": unit,
                    "target": target,
                    "function": data.catalogue[target]["function"],
                    **a3c.recommend(data, target, row, train, generalist),
                }
            )
    return pd.DataFrame(rows)


def _compare(a, b):
    difference = a - b
    nonzero = (difference.abs() > 1e-12).any()
    return {
        "mean": round(float(difference.mean()), 4),
        "median": round(float(difference.median()), 4),
        "wins_losses": [int((difference > 1e-9).sum()), int((difference < -1e-9).sum())],
        "p_two_sided": float(wilcoxon(a, b).pvalue) if nonzero else 1.0,
    }


def per_function_means(long, columns):
    """Each function's mean over its targets and samples, per split."""
    return long.groupby(["split", "function"])[columns].mean().reset_index()


def seed_noise(catalogue, configs, bounds):
    """Standard error over the seeds of every matrix cell's HVn at the final budget."""
    reference = np.full(2, a3c.REFERENCE)
    errors = {}
    for q in catalogue:
        ideal = np.asarray(bounds[q]["ideal"])
        span = np.asarray(bounds[q]["nadir"]) - ideal
        fronts = {c: np.load(a3c.MATRIX / f"{c}__{q}.npz") for c in configs}
        final = [f"s{s}_e{a3c.FINAL}" for s in a3c.SEEDS]
        union = np.vstack([fronts[c][k] for c in configs for k in final])
        union = union[a3c.moocore.is_nondominated(union, keep_weakly=False)]
        best = a3c._hv((union - ideal) / span, reference)
        for c in configs:
            values = [a3c._hv((fronts[c][k] - ideal) / span, reference) / best for k in final]
            errors[(c, q)] = float(np.std(values, ddof=1) / np.sqrt(len(values)))
    return pd.Series(errors)


def main() -> None:
    """Compute every secondary analysis and write data/secondary.json."""
    catalogue = json.loads((a3c.DATA / "catalogue.json").read_text())
    bounds = json.loads((a3c.DATA / "tuning_bounds.json").read_text())
    samples = pd.read_csv(a3c.DATA / "features_sample_scaled.csv")
    raw_samples = pd.read_csv(a3c.DATA / "features_raw_objectives.csv")
    hvn = pd.read_csv(a3c.DATA / "hvn.csv")
    long = pd.read_csv(a3c.DATA / "transfer_long.csv")
    configs = [f"tuned__f{f:02d}" for f in range(1, 56)] + a3c.GENERALISTS + a3c.DEFAULTS
    data = a3c.Data(catalogue, samples, hvn)
    raw = a3c.Data(catalogue, raw_samples, hvn)
    out = {}

    loss = long[a3c.METHODS].rsub(long["oracle"], axis=0)
    out["mean_worst_10pct_loss_vs_oracle"] = {
        split: {
            m: round(float(np.sort(x[m].dropna())[-max(1, len(x[m].dropna()) // 10) :].mean()), 4)
            for m in a3c.METHODS
            if x[m].notna().any()
        }
        for split, x in loss.assign(split=long.split).groupby("split")
    }

    f = per_function_means(long, a3c.METHODS)
    s1 = f[f.split == "S1"].set_index("function")
    out["ceiling_S1"] = {
        "same_function_vs_generalist": _compare(s1.same_function, s1.generalist),
        "same_function_vs_sbs": _compare(s1.same_function, s1.sbs),
        "sbs_vs_generalist": _compare(s1.sbs, s1.generalist),
    }
    s2 = f[f.split == "S2"].set_index("function")
    out["S2_sbs_vs_generalist"] = _compare(s2.sbs, s2.generalist)

    rows = []
    for split, _unit, target, train, _ in a3c.splits(data):
        for row in np.flatnonzero(data.sample_problem == target):
            rows.append(
                {
                    "split": split,
                    "function": catalogue[target]["function"],
                    **distance_picks(data, raw, row, train),
                }
            )
    picks = pd.DataFrame(rows)
    assert np.allclose(picks.euclidean.to_numpy(), long.landscape_1nn.to_numpy())
    out["distances_mean_hvn_over_functions"] = (
        per_function_means(picks, DISTANCES)
        .groupby("split")[DISTANCES]
        .mean()
        .round(4)
        .to_dict(orient="index")
    )

    budgets = {}
    for budget in (5000, 10000):
        a3c.FINAL = budget
        data_b = a3c.Data(catalogue, samples, a3c.hvn_table(list(catalogue), configs, bounds))
        long_b = run_pipeline(data_b)
        f_b = per_function_means(long_b, a3c.METHODS)
        s1_b = f_b[f_b.split == "S1"].set_index("function")
        s2_b = f_b[f_b.split == "S2"].set_index("function")
        budgets[str(budget)] = {
            "mean_hvn_over_functions": f_b.groupby("split")[a3c.METHODS]
            .mean()
            .round(4)
            .to_dict(orient="index"),
            "G4_comparison": _compare(s1_b.landscape_1nn, s1_b.generalist),
            "G5_comparison": _compare(s2_b.consensus, s2_b.generalist),
            "consensus_deviates_from_sbs": float(long_b.consensus_deviates.mean()),
        }
    a3c.FINAL = 20_000
    out["budgets"] = budgets

    errors = seed_noise(catalogue, configs, bounds)
    kinds = errors.index.get_level_values(0).str.split("__").str[0]
    out["seed_standard_error"] = {
        kind: {
            "median": round(float(errors[kinds == kind].median()), 5),
            "p90": round(float(errors[kinds == kind].quantile(0.9)), 5),
        }
        for kind in ("tuned", "gen", "default")
    }

    (a3c.DATA / "secondary.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
