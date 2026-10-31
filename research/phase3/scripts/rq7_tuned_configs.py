"""RQ7, exploratory: what do the tuned configurations choose, and do the features explain it?

plan.md section 11, D10; 2026-10-31.

Data: the 37 elites of phase 3 (data/tuned_configs.json), the 49 features (MOLA 0.4.0, `sample`
objective scaling; problem means over the 5 LHS samples) and the phase 3 matrix.

1. Choices: the distribution of every top-level parameter, overall and by family, and the elites at
   a bound of the space (within 5 % of its range).
2. Mantel tests (Spearman, one-sided, 9 999 permutations of the problem labels, seed 20261031):
   does the distance between problems predict the distance between their configurations?
   Problem distances: landscape (Euclidean on robust-scaled feature means) and metadata (as in
   analyze_transfer). Configuration distances:
   - parameters: Gower over the 9 top-level parameters (pop_size on a log scale);
   - behaviour: 1 - Spearman correlation of the two configurations' HVn over the 37 problems;
   - mutual transfer loss: (L(a -> b) + L(b -> a)) / 2,
     with L(a -> b) = HVn(c*_b, b) - HVn(c*_a, b).
   Each test runs on all pairs and on the pairs from different families only (the pair set is
   fixed by the true labels; the permutation moves the configuration matrix).
3. Prediction of each parameter from the features, leaving one formulation group out (32 folds):
   a random forest (500 trees, random_state 0) and the nearest training problem (1-NN, the transfer
   mechanism), against the training majority class (categorical) or median (numeric). Features are
   robust-scaled with the training problems only. For categorical parameters a second
   baseline draws from the training frequencies (expected accuracy), because the majority
   class is anti-correlated with the left-out answer when two classes tie.

Run locally:  MOLA_PHASE3_MATRIX=... python research/phase3/scripts/rq7_tuned_configs.py
Writes data/rq7_tuned_configs.json. scikit-learn 1.9.1.
"""

import json

import analyze_transfer as at
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

CATEGORICAL = ["offspring_ratio", "selection", "initializer", "crossover", "mutation", "repair"]
NUMERIC = {
    "pop_size": (20, 200, True),
    "crossover_prob": (0.6, 1.0, False),
    "mutation_prob_factor": (0.25, 3.0, False),
}  # (low, high, log scale)
PERMUTATIONS, SEED = 9999, 20261031


def _scale(values, low, high, log):
    if log:
        return (np.log(values) - np.log(low)) / (np.log(high) - np.log(low))
    return (values - low) / (high - low)


def gower(configs: pd.DataFrame) -> np.ndarray:
    n = len(configs)
    total = np.zeros((n, n))
    for name in CATEGORICAL:
        v = configs[name].astype(str).to_numpy()
        total += v[:, None] != v[None, :]
    for name, (low, high, log) in NUMERIC.items():
        v = _scale(configs[name].astype(float).to_numpy(), low, high, log)
        total += np.abs(v[:, None] - v[None, :])
    return total / (len(CATEGORICAL) + len(NUMERIC))


def mantel(a: np.ndarray, b: np.ndarray, pairs: np.ndarray, rng) -> dict:
    """Spearman between a[pairs] and b[pairs]; p from permuting b's labels (one-sided, > 0)."""
    i, j = pairs
    observed = spearmanr(a[i, j], b[i, j]).statistic
    n = len(a)
    count = 0
    for _ in range(PERMUTATIONS):
        p = rng.permutation(n)
        count += spearmanr(a[i, j], b[p][:, p][i, j]).statistic >= observed
    return {
        "rho": round(float(observed), 3),
        "p": round((count + 1) / (PERMUTATIONS + 1), 4),
        "pairs": int(len(i)),
    }


def robust(train_means, query):
    q75, median, q25 = np.percentile(train_means, [75, 50, 25], axis=0)
    iqr = q75 - q25
    keep = iqr > 0
    return (train_means[:, keep] - median[keep]) / iqr[keep], (query[keep] - median[keep]) / iqr[
        keep
    ]


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
    tuned = json.loads((at.DATA_DIR / "tuned_configs.json").read_text())
    configs = pd.DataFrame([tuned[p]["config"] for p in problems], index=problems)
    configs["offspring_ratio"] = configs["offspring_ratio"].astype(float)
    fam = pd.Series(family)
    n = len(problems)
    result = {"note": "Exploratory (RQ7, D10). n = 37 problems: low power."}

    # 1. Choices
    choices = {"categorical": {}, "numeric": {}, "by_family": {}}
    for name in CATEGORICAL:
        choices["categorical"][name] = configs[name].astype(str).value_counts().to_dict()
        choices["by_family"][name] = {
            f: configs.loc[fam[fam == f].index, name].astype(str).value_counts().to_dict()
            for f in sorted(fam.unique())
        }
    for name, (low, high, log) in NUMERIC.items():
        v = configs[name].astype(float)
        s = _scale(v.to_numpy(), low, high, log)
        choices["numeric"][name] = {
            "median": round(float(v.median()), 3),
            "q25": round(float(v.quantile(0.25)), 3),
            "q75": round(float(v.quantile(0.75)), 3),
            "at_lower_bound": int((s <= 0.05).sum()),
            "at_upper_bound": int((s >= 0.95).sum()),
        }
    result["choices"] = choices

    # 2. Mantel
    values = ctx.means[:, np.isfinite(ctx.means).all(axis=0)]
    z, _ = robust(values, values[0])
    landscape = np.linalg.norm(z[:, None] - z[None], axis=2)
    meta = ctx.meta
    sd = meta.std(axis=0, ddof=1)
    sd[sd == 0] = 1.0
    metadata = np.linalg.norm((meta[:, None] - meta[None]) / sd, axis=2)
    S = ctx.score  # S[a, b]: HVn of c*_a on b
    behaviour = 1 - spearmanr(S, axis=1).statistic
    loss = np.diag(S)[None, :] - S  # loss[a, b] = L(a -> b)
    mutual = (loss + loss.T) / 2
    parameters = gower(configs)
    upper = np.triu_indices(n, k=1)
    different = np.array(
        [family[problems[a]] != family[problems[b]] for a, b in zip(*upper, strict=True)]
    )
    sets = {"all_pairs": upper, "between_families": (upper[0][different], upper[1][different])}
    rng = np.random.default_rng(SEED)
    result["mantel"] = {
        problem_name: {
            config_name: {s: mantel(problem_d, config_d, pairs, rng) for s, pairs in sets.items()}
            for config_name, config_d in [
                ("parameters_gower", parameters),
                ("behaviour", behaviour),
                ("mutual_transfer_loss", mutual),
            ]
        }
        for problem_name, problem_d in [("landscape", landscape), ("metadata", metadata)]
    }

    # 3. Prediction, leaving one formulation group out
    rows = []
    for g in sorted(set(group.values())):
        test = [i for i, p in enumerate(problems) if group[p] == g]
        train = [i for i, p in enumerate(problems) if group[p] != g]
        for t in test:
            x_train, x_query = robust(values[train], values[t])
            nearest = train[int(np.argmin(np.linalg.norm(x_train - x_query, axis=1)))]
            for name in CATEGORICAL:
                y = configs[name].astype(str).to_numpy()
                y_train = y[train]
                if len(set(y_train)) > 1:
                    model = RandomForestClassifier(n_estimators=500, random_state=0).fit(
                        x_train, y_train
                    )
                    rf = model.predict(x_query[None, :])[0]
                else:
                    rf = y_train[0]
                majority = pd.Series(y_train).mode().iloc[0]
                rows.append(
                    {
                        "parameter": name,
                        "kind": "categorical",
                        "target": problems[t],
                        "rf": float(rf == y[t]),
                        "nn1": float(y[nearest] == y[t]),
                        "baseline": float(majority == y[t]),
                        "baseline_frequency": float(np.mean(y_train == y[t])),
                    }
                )
            for name, (low, high, log) in NUMERIC.items():
                y = _scale(configs[name].astype(float).to_numpy(), low, high, log)
                model = RandomForestRegressor(n_estimators=500, random_state=0).fit(
                    x_train, y[train]
                )
                rows.append(
                    {
                        "parameter": name,
                        "kind": "numeric",
                        "target": problems[t],
                        "rf": float(abs(model.predict(x_query[None, :])[0] - y[t])),
                        "nn1": float(abs(y[nearest] - y[t])),
                        "baseline": float(abs(np.median(y[train]) - y[t])),
                        "baseline_frequency": np.nan,
                    }
                )
    pred = pd.DataFrame(rows)
    result["prediction_logo"] = {
        "note": "categorical: accuracy (higher is better); numeric: mean absolute error on the "
        "[0, 1]-scaled range (lower is better)",
        **{
            name: x[["rf", "nn1", "baseline", "baseline_frequency"]]
            .mean()
            .round(3)
            .dropna()
            .to_dict()
            for name, x in pred.groupby("parameter")
        },
    }
    (at.DATA_DIR / "rq7_tuned_configs.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("mantel", "prediction_logo")}, indent=1))
    print(json.dumps(result["choices"]["numeric"], indent=1))


if __name__ == "__main__":
    main()
