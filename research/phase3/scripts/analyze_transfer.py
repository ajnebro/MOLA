"""Phase 3, pre-registered analysis (preregistration.md): does landscape similarity transfer?

Inputs
- The performance matrix: each portfolio configuration (the 37 irace-tuned c*_P and the NSGA-II,
  MOEA/D and SMS-EMOA defaults) on each development problem, evaluation seeds 5001-5010,
  20 000 evaluations (MATRIX/<config>__<problem>.npz).
- MOLA features of each problem from 5 independent LHS samples (bound geometry, k = D). Since
  amendment 1 (preregistration.md section 9) every landscape method uses the features computed
  with objective scaling `sample` (data/features_sample_scaled.csv, MOLA 0.4.0); the raw-objective
  features of phase 2 (phase2/data/pilot_features.csv) only feed the secondary
  landscape_1nn_raw_objectives.

HVn. Fronts are min-max normalized by the problem's true-front ideal and nadir
(data/tuning_bounds.json), reference point 1.1, and divided by the HV of the union of every final
front of the matrix on that problem.

Methods. For a target Q (characterized by one of its 5 samples) and a training set T of other
problems, the candidates are the c*_P with P in T. HVn(c, Q) is the mean over the 10 seeds.
- sbs: the candidate with the best mean HVn over T.
- metadata_1nn: c*_P of the nearest P by metadata (log D, mean and std of log bound ranges).
- random: the expected HVn of a uniformly random donor.
- thesis_1nn: c*_P of the nearest P by the thesis distance (eq. 4.1) on its 19 features,
  undefined terms skipped.
- landscape_1nn: c*_P of the nearest P by Euclidean distance on the 49 features robust-scaled
  (median, IQR over T's samples), features undefined anywhere in T or Q dropped. **Primary
  landscape method.**
- loss_predictor: ridge regression (lambda = 1) of the transfer loss L(A->B) on
  |z(A) - z(B)| over ordered pairs within T, then the donor with the least predicted loss.
- knn_selector: the candidate with the best mean HVn over Q's 3 nearest problems in T (same
  distance as landscape_1nn) -- a direct selector using the same features.
- landscape_1nn_raw_objectives (secondary, amendment 1): landscape_1nn on the raw-objective
  features, to show what the objective scaling changes.
References: oracle (best candidate on Q), self (c*_Q), default (NSGA-II default).
Training problems are represented by the mean of their 5 samples.

Splits: LOGO (formulation group out, groups with the LZ09/UF relatives merged), LOFO (family
out), and 100 random problem-level 80/20 splits (seed 20261021) ignoring groups.

G3 (LOGO): landscape_1nn beats metadata_1nn if the per-group mean of
HVn(landscape_1nn) - HVn(metadata_1nn) is positive with a one-sided Wilcoxon signed-rank p < 0.05
over groups.

Run locally:  python research/phase3/scripts/analyze_transfer.py
Writes data/transfer_long.csv, data/transfer_summary.csv and data/g3_result.json.
"""

import json
import os
import sys
from pathlib import Path

import moocore
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "phase2" / "scripts"))

from common import DATA as PHASE2_DATA  # noqa: E402
from common import PHASE as PHASE2  # noqa: E402
from common import bounds, instantiate, pilot_problems  # noqa: E402

PHASE3 = HERE.parent
MATRIX = Path(os.environ.get("MOLA_PHASE3_MATRIX", r"C:\tmp\mola-phase3\matrix\fronts"))
SEEDS = tuple(range(5001, 5011))
FINAL = 20_000
REFERENCE = 1.1
DEFAULTS = ("default__nsgaii", "default__moead", "default__smsemoa")
META = {"problem", "seed", "n", "D", "M", "geometry", "k", "nd_count", "evaluation_seconds",
        "characterization_seconds", "undefined", "objective_scaling", "mola_version"}
PRIMARY_FEATURES = PHASE3 / "data" / "features_sample_scaled.csv"
RAW_OBJECTIVE_FEATURES = PHASE2_DATA / "pilot_features.csv"
THESIS19 = ["dist_x_avg", "dist_x_max", "dist_f_avg", "dist_f_max", "nd_n", "dist_x_nd_avg",
            "dist_x_nd_max", "rank_avg", "rank_max", "rank_ent", "sup_avg_neig", "inf_avg_neig",
            "inc_avg_neig", "lnd_avg_neig", "lsupp_avg_neig", "dist_x_avg_neig", "dist_f_avg_neig",
            "dist_x_cor_neig", "dist_f_cor_neig"]
# Structural LZ09/UF relatives (stage A, phase 2: 1-NN confusions between their samples).
RELATIVES = [{"cec2009_uf1", "lz09_f2", "lz09_f9"}, {"cec2009_uf2", "lz09_f5"}, {"lz09_f7", "lz09_f8"}]
RANDOM_SPLITS, RANDOM_SEED, TRAIN_FRACTION = 100, 20261021, 0.8
METHODS = ("sbs", "metadata_1nn", "random", "thesis_1nn", "landscape_1nn", "loss_predictor",
           "knn_selector", "landscape_1nn_raw_objectives", "oracle", "self", "default")


# --------------------------------------------------------------------------------------------- data
def groups_and_families(problems):
    catalogue = pd.read_csv(PHASE2 / "catalogue.csv").set_index("problem")
    group = {p: catalogue.loc[p, "group"] for p in problems}
    for relatives in RELATIVES:
        label = "+".join(sorted(relatives))
        for p in relatives:
            group[p] = label
    family = {p: catalogue.loc[p, "family"] for p in problems}
    return group, family


def metadata(problems) -> pd.DataFrame:
    rows = {}
    for p in problems:
        lower, upper = bounds(instantiate(p))
        log_range = np.log10(upper - lower)
        rows[p] = {"log_d": np.log10(len(lower)), "mean_log_range": log_range.mean(),
                   "std_log_range": log_range.std()}
    return pd.DataFrame(rows).T


def hvn_matrix(problems) -> dict[tuple[str, str], np.ndarray]:
    """(config, problem) -> HVn per seed at the final budget."""
    tuned_bounds = json.loads((PHASE3 / "data" / "tuning_bounds.json").read_text())
    configs = [f"tuned__{p}" for p in problems] + list(DEFAULTS)
    out = {}
    for problem in problems:
        ideal = np.asarray(tuned_bounds[problem]["ideal"])
        span = np.asarray(tuned_bounds[problem]["nadir"]) - ideal
        reference = np.full(len(ideal), REFERENCE)
        fronts = {c: np.load(MATRIX / f"{c}__{problem}.npz") for c in configs}

        def hv(front):
            scaled = (front - ideal) / span
            scaled = scaled[np.all(scaled < reference, axis=1)]
            return float(moocore.hypervolume(scaled, ref=reference)) if len(scaled) else 0.0

        union = np.vstack([fronts[c][f"s{s}_e{FINAL}"] for c in configs for s in SEEDS])
        best = hv(union[moocore.is_nondominated(union, keep_weakly=False)])
        for c in configs:
            out[(c, problem)] = np.array([hv(fronts[c][f"s{s}_e{FINAL}"]) / best for s in SEEDS])
    return out


# ---------------------------------------------------------------------------------------- methods
class Context:
    """Arrays shared by every recommendation (problems indexed in pilot order)."""

    def __init__(self, problems, samples: pd.DataFrame, raw_samples: pd.DataFrame,
                 meta: pd.DataFrame, hvn: dict):
        self.problems = problems
        index = {p: i for i, p in enumerate(problems)}
        if not (samples[["problem", "seed"]].to_numpy() == raw_samples[["problem", "seed"]].to_numpy()).all():
            raise ValueError("the two feature tables must list the same samples in the same order")
        self.features = [c for c in samples.columns if c not in META]
        self.thesis_columns = [self.features.index(c) for c in THESIS19]
        self.sample_problem = samples["problem"].map(index).to_numpy()
        self.sample_values = samples[self.features].to_numpy(float)
        self.raw_values = raw_samples[self.features].to_numpy(float)
        self.means = self._means(self.sample_values, len(problems))
        self.raw_means = self._means(self.raw_values, len(problems))
        self.meta = meta.loc[problems].to_numpy(float)
        # score[a, b]: mean HVn of c*_a on problem b; default[b]: NSGA-II default on b.
        self.score = np.array([[hvn[(f"tuned__{a}", b)].mean() for b in problems] for a in problems])
        self.default = np.array([hvn[("default__nsgaii", b)].mean() for b in problems])

    def _means(self, values: np.ndarray, count: int) -> np.ndarray:
        return np.vstack([np.nanmean(values[self.sample_problem == i], axis=0) for i in range(count)])


def _robust_z(values, means, sample_problem, query, train):
    """Training means and query robust-scaled over T's samples (median, IQR); usable features only."""
    train_rows = values[np.isin(sample_problem, train)]
    defined = np.isfinite(train_rows).all(axis=0) & np.isfinite(query)
    q75, median, q25 = np.percentile(train_rows[:, defined], [75, 50, 25], axis=0)
    iqr = q75 - q25
    keep = np.flatnonzero(defined)[iqr > 0]
    median, iqr = median[iqr > 0], iqr[iqr > 0]
    return (means[train][:, keep] - median) / iqr, (query[keep] - median) / iqr


def recommend(ctx: Context, target: int, row: int, train: np.ndarray) -> dict:
    """HVn on the target of the configuration each method recommends (mean over seeds).

    `row` is the target sample's row in the feature tables.
    """
    on_target = ctx.score[train, target]
    query = ctx.sample_values[row]
    z_train, z_query = _robust_z(ctx.sample_values, ctx.means, ctx.sample_problem, query, train)
    landscape = np.linalg.norm(z_train - z_query, axis=1)
    raw_train, raw_query = _robust_z(ctx.raw_values, ctx.raw_means, ctx.sample_problem,
                                     ctx.raw_values[row], train)
    landscape_raw = np.linalg.norm(raw_train - raw_query, axis=1)

    meta_train = ctx.meta[train]
    mu, sd = meta_train.mean(axis=0), meta_train.std(axis=0, ddof=1)
    sd[sd == 0] = 1.0
    meta_distance = np.linalg.norm((meta_train - ctx.meta[target]) / sd, axis=1)

    a, b = ctx.means[train][:, ctx.thesis_columns], query[ctx.thesis_columns]
    with np.errstate(divide="ignore", invalid="ignore"):
        ratio = np.where(b < a, b / a, a / b)
    thesis = np.nansum(np.abs(1 - ratio), axis=1)

    within = ctx.score[np.ix_(train, train)]
    generalist = within.mean(axis=1)

    # Transfer-loss predictor: ridge (lambda = 1) on |z(A) - z(B)| over ordered pairs within T.
    n = len(train)
    off_diagonal = ~np.eye(n, dtype=bool)
    x = np.abs(z_train[:, None, :] - z_train[None, :, :])[off_diagonal]
    y = (np.diag(within)[None, :] - within)[off_diagonal]  # L(A -> B) = HVn(c*_B, B) - HVn(c*_A, B)
    x_mu, x_sd = x.mean(axis=0), x.std(axis=0)
    x_sd[x_sd == 0] = 1.0
    xs = np.c_[np.ones(len(x)), (x - x_mu) / x_sd]
    penalty = np.eye(xs.shape[1])
    penalty[0, 0] = 0.0
    beta = np.linalg.solve(xs.T @ xs + penalty, xs.T @ y)
    predicted = np.c_[np.ones(n), (np.abs(z_train - z_query) - x_mu) / x_sd] @ beta

    nearest3 = np.argsort(landscape, kind="stable")[:3]
    selector = within[:, nearest3].mean(axis=1)

    return {
        "sbs": on_target[np.argmax(generalist)],
        "metadata_1nn": on_target[np.argmin(meta_distance)],
        "random": float(on_target.mean()),
        "thesis_1nn": on_target[np.argmin(thesis)],
        "landscape_1nn": on_target[np.argmin(landscape)],
        "loss_predictor": on_target[np.argmin(predicted)],
        "knn_selector": on_target[np.argmax(selector)],
        "landscape_1nn_raw_objectives": on_target[np.argmin(landscape_raw)],
        "oracle": float(on_target.max()),
        "self": float(ctx.score[target, target]),
        "default": float(ctx.default[target]),
        "landscape_donor": ctx.problems[train[np.argmin(landscape)]],
    }


# ------------------------------------------------------------------------------------------ splits
def splits(problems, group, family):
    for g in sorted(set(group.values())):
        targets = [p for p in problems if group[p] == g]
        yield "LOGO", g, targets, [p for p in problems if group[p] != g]
    for f in sorted(set(family.values())):
        targets = [p for p in problems if family[p] == f]
        yield "LOFO", f, targets, [p for p in problems if family[p] != f]
    rng = np.random.default_rng(RANDOM_SEED)
    for rep in range(RANDOM_SPLITS):
        order = list(rng.permutation(problems))
        cut = int(round(TRAIN_FRACTION * len(order)))
        yield "random", str(rep), order[cut:], order[:cut]


def main() -> None:
    problems = pilot_problems()
    group, family = groups_and_families(problems)
    samples = pd.read_csv(PRIMARY_FEATURES)
    raw_samples = pd.read_csv(RAW_OBJECTIVE_FEATURES)
    ctx = Context(problems, samples, raw_samples, metadata(problems), hvn_matrix(problems))
    index = {p: i for i, p in enumerate(problems)}

    rows = []
    for split, unit, targets, train in splits(problems, group, family):
        train_index = np.array([index[p] for p in train])
        for target in targets:
            for row in np.flatnonzero(ctx.sample_problem == index[target]):
                result = recommend(ctx, index[target], row, train_index)
                rows.append({"split": split, "unit": unit, "target": target, "group": group[target],
                             "family": family[target], "sample": int(samples.loc[row, "seed"]),
                             **result})
    long = pd.DataFrame(rows)
    long.to_csv(PHASE3 / "data" / "transfer_long.csv", index=False)

    per_target = long.groupby(["split", "unit", "target", "group"])[list(METHODS)].mean().reset_index()
    summary = per_target.groupby("split")[list(METHODS)].mean().T
    summary.to_csv(PHASE3 / "data" / "transfer_summary.csv")

    logo = per_target[per_target.split == "LOGO"].groupby("group")[list(METHODS)].mean()
    difference = logo["landscape_1nn"] - logo["metadata_1nn"]
    test = wilcoxon(logo["landscape_1nn"], logo["metadata_1nn"], alternative="greater", zero_method="wilcox")
    stable = long[long.split == "LOGO"].groupby("target").landscape_donor.nunique()
    discriminative = logo.index[(logo["oracle"] - logo["sbs"]) >= 0.01]
    result = {
        "g3_rule": "LOGO: landscape_1nn > metadata_1nn, one-sided Wilcoxon over groups, p < 0.05",
        "groups": int(len(logo)),
        "mean_difference": float(difference.mean()), "median_difference": float(difference.median()),
        "wins_losses_ties": [int((difference > 1e-9).sum()), int((difference < -1e-9).sum()),
                             int((difference.abs() <= 1e-9).sum())],
        "wilcoxon_p": float(test.pvalue), "g3_passes": bool(test.pvalue < 0.05 and difference.mean() > 0),
        "logo_mean_hvn": logo.mean().round(4).to_dict(),
        "logo_discriminative_groups": list(map(str, discriminative)),
        "logo_mean_hvn_discriminative": logo.loc[discriminative].mean().round(4).to_dict(),
        "landscape_donor_identical_across_samples": float((stable == 1).mean()),
        "gain_vs_sbs_by_split": {s: float((per_target[per_target.split == s]["landscape_1nn"]
                                           - per_target[per_target.split == s]["sbs"]).mean())
                                 for s in ("LOGO", "LOFO", "random")},
    }
    (PHASE3 / "data" / "g3_result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    print(summary.round(4).to_string())


if __name__ == "__main__":
    main()
