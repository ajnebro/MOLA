"""Global landscape features (paper §4.1.1, Table 1).

Each function takes exactly the precomputed substrate pieces it needs (a normalizer, a ranking, a
neighbourhood, ...) rather than a whole Sample, so it stays testable and reasoned about in
isolation. An orchestrator that builds the shared substrate once per sample and calls every
feature belongs here once enough features exist to justify one.
"""

from itertools import combinations

import numpy as np
from scipy.spatial import ConvexHull, QhullError
from scipy.spatial.distance import pdist
from scipy.stats import entropy, spearmanr

from mola.distance import pairwise_distance_stats
from mola.normalization import Normalizer
from mola.ranking import Ranking

_SUPPORTED_FACET_TOLERANCE = 1e-9
"""Floating-point slack for `supp_n`'s "outward normal entirely <= 0" facet test."""


def f_cor(objectives: np.ndarray) -> float:
    """Correlation among objective values measured on the sample (Table 1: f_cor).

    For M=2 (the paper's own bi-objective benchmark), a single Spearman correlation between the
    two objective columns. **MOLA's own extension, beyond the paper's literal scope**: for M>2,
    the mean of the C(M,2) pairwise Spearman correlations — signed, not `abs()`, since a negative
    pairwise correlation is a real conflicting-objectives signal that averaging magnitudes would
    destroy (Design decisions). Reduces to the paper's own definition at M=2.

    Args:
        objectives: Objective vectors, shape (n, M), with n >= 2 and M >= 2.

    Returns:
        The (mean pairwise) Spearman correlation. NaN if any objective column is constant
        (zero variance — the correlation is undefined), propagated from `scipy.stats.spearmanr`
        rather than special-cased.
    """
    number_of_objectives = objectives.shape[1]
    correlations = [
        spearmanr(objectives[:, i], objectives[:, j]).statistic
        for i, j in combinations(range(number_of_objectives), 2)
    ]
    return float(np.mean(correlations))


def dist_x_avg(variables: np.ndarray, normalizer: Normalizer) -> float:
    """Average pairwise distance among sampled solutions in variable space (Table 1: dist_x_avg).

    Normalized against the whole sample's own variable-space distance range, per Design
    decisions ("Normalization reference") — `normalizer` must be built from these same
    `variables` (see `mola.normalization.build_normalizers`).

    Args:
        variables: Decision vectors, shape (n, D), with n >= 2.
        normalizer: The variable-space normalizer for this sample.

    Returns:
        The normalized average pairwise variable-space distance, in [0, 1].
    """
    return normalizer.normalize(pairwise_distance_stats(variables).mean)


def dist_x_max(variables: np.ndarray) -> float:
    """Maximum pairwise distance among sampled solutions in variable space (Table 1: dist_x_max).

    Reported raw, not normalized — every `*_MAX` feature stays raw (Design decisions,
    "Normalization reference").

    Args:
        variables: Decision vectors, shape (n, D), with n >= 2.

    Returns:
        The raw maximum pairwise variable-space distance.
    """
    return pairwise_distance_stats(variables).maximum


def dist_f_avg(objectives: np.ndarray, normalizer: Normalizer) -> float:
    """Average pairwise distance among sampled solutions in objective space (Table 1: dist_f_avg).

    Normalized against the whole sample's own OBJECTIVE-space distance range — `normalizer` must
    be the F-space one. MOORPHOLOGY's equivalent normalizes this with a minimum derived from
    variable-space distance instead (`ProblemCharacterization.java:160`) — redesigned here on the
    correct normalizer, not ported (Audit section).

    Args:
        objectives: Objective vectors, shape (n, M), with n >= 2.
        normalizer: The objective-space normalizer for this sample.

    Returns:
        The normalized average pairwise objective-space distance, in [0, 1].
    """
    return normalizer.normalize(pairwise_distance_stats(objectives).mean)


def dist_f_max(objectives: np.ndarray) -> float:
    """Maximum pairwise distance among sampled solutions in objective space (Table 1: dist_f_max).

    Reported raw, not normalized — every `*_MAX` feature stays raw (Design decisions,
    "Normalization reference").

    Args:
        objectives: Objective vectors, shape (n, M), with n >= 2.

    Returns:
        The raw maximum pairwise objective-space distance.
    """
    return pairwise_distance_stats(objectives).maximum


def nd_n(ranking: Ranking) -> float:
    """Proportion of non-dominated solutions among the sample (Table 1: nd_n).

    Args:
        ranking: The sample's non-dominated ranking.

    Returns:
        |non-dominated| / n, in the interval (0, 1].
    """
    return ranking.nondominated.size / ranking.rank.size


def dist_x_nd_avg(variables: np.ndarray, ranking: Ranking, normalizer: Normalizer) -> float:
    """Average pairwise distance among non-dominated solutions in variable space (Table 1).

    Normalized against the whole sample's own variable-space distance range — never a range
    recomputed over the non-dominated subset (Design decisions, "Normalization reference").
    MOORPHOLOGY's equivalent (`distanceXNonDominatedAverage`) has the same pair-filter bug as
    `distanceXNonDominatedMaximum`, plus a wrong divisor (a per-solution count instead of a pair
    count, line 173) — redesigned here directly on `ranking.nondominated`, not ported (Audit
    section).

    Args:
        variables: Decision vectors, shape (n, D).
        ranking: The sample's non-dominated ranking, built from these same `variables`.
        normalizer: The variable-space normalizer for this sample.

    Returns:
        The normalized average pairwise distance among non-dominated solutions, or NaN if fewer
        than 2 solutions are non-dominated (see `dist_x_nd_max`).
    """
    nondominated = variables[ranking.nondominated]
    if nondominated.shape[0] < 2:
        return float("nan")
    return normalizer.normalize(pairwise_distance_stats(nondominated).mean)


def dist_x_nd_max(variables: np.ndarray, ranking: Ranking) -> float:
    """Maximum pairwise distance among non-dominated solutions in variable space (Table 1).

    Reported raw, not normalized — every `*_MAX` feature stays raw (Design decisions,
    "Normalization reference"). MOORPHOLOGY's equivalent (`distanceXNonDominatedMaximum`) has a
    pair-filter bug (checks the same sample index against itself, not against the other member of
    the pair) — redesigned here directly on `ranking.nondominated`, not ported (Audit section).

    Args:
        variables: Decision vectors, shape (n, D).
        ranking: The sample's non-dominated ranking, built from these same `variables`.

    Returns:
        The raw maximum pairwise distance among non-dominated solutions, or NaN if fewer than 2
        solutions are non-dominated (no pair to measure — possible in principle, though `nd_n`'s
        own lower bound makes it very unlikely at the paper's sampling rate).
    """
    nondominated = variables[ranking.nondominated]
    if nondominated.shape[0] < 2:
        return float("nan")
    return pairwise_distance_stats(nondominated).maximum


def rank_avg(ranking: Ranking) -> float:
    """Average rank with respect to non-dominated sorting (Table 1: rank_avg).

    Rank is zero-based — rank 0 is the non-dominated front — following
    `mola.ranking.rank_solutions`'s own convention.

    Args:
        ranking: The sample's non-dominated ranking.

    Returns:
        The mean per-solution rank.
    """
    return float(ranking.rank.mean())


def rank_max(ranking: Ranking) -> float:
    """Maximum rank with respect to non-dominated sorting (Table 1: rank_max).

    Rank is zero-based — rank 0 is the non-dominated front — following
    `mola.ranking.rank_solutions`'s own convention.

    Args:
        ranking: The sample's non-dominated ranking.

    Returns:
        The largest per-solution rank, equivalently `ranking.number_of_fronts - 1`.
    """
    return float(ranking.rank.max())


def rank_ent(ranking: Ranking) -> float:
    """Entropy of the distribution of solutions per rank (Table 1: rank_ent).

    Shannon entropy, base 2 (bits), of the front-size proportions. The paper does not state a
    log base; this matches MOORPHOLOGY's `getRankEntropy` exactly
    (`ProblemCharacterization.java:384-403`, confirmed by reading its source, not assumed).

    Args:
        ranking: The sample's non-dominated ranking.

    Returns:
        The base-2 entropy of the front-size distribution, in bits. Zero when every solution
        falls in a single front.
    """
    front_sizes = [front.size for front in ranking.fronts]
    return float(entropy(front_sizes, base=2))


def fdc(variables: np.ndarray, objectives: np.ndarray, ranking: Ranking) -> float:
    """Fitness-distance correlation among non-dominated solutions (Table 1: fdc).

    Spearman correlation between pairwise variable-space distance and pairwise objective-space
    distance, over all C(k,2) pairs among the k=|ND| solutions (Design decisions; "denoted as
    fitness-distance-correlation in [18]", §4.1.1). Distinct from ruggedness's
    `dist_x_cor_neig`/`dist_f_cor_neig` (a per-solution average-distance-to-neighbours measure
    across neighbour pairs over the *whole* sample) and from evolvability's
    `dist_f_dist_x_avg_neig` (a ratio, not a correlation).

    Args:
        variables: Decision vectors, shape (n, D).
        objectives: Objective vectors, shape (n, M), over the same solutions as `variables`.
        ranking: The sample's non-dominated ranking.

    Returns:
        The Spearman correlation between pairwise X-distance and F-distance among non-dominated
        solutions. NaN if fewer than 2 solutions are non-dominated — zero pairs, propagated from
        `scipy.stats.spearmanr` rather than special-cased.
    """
    nondominated = ranking.nondominated
    x_distances = pdist(variables[nondominated])
    f_distances = pdist(objectives[nondominated])
    return float(spearmanr(x_distances, f_distances).statistic)


def supp_n(objectives: np.ndarray, ranking: Ranking) -> float:
    """Proportion of supported non-dominated solutions (Table 1: supp_n).

    Supported = on the convex hull of the non-dominated subset's objective vectors, findable by
    minimizing some linear scalarization (classical definition, Ehrgott [10], §4.1.1). The
    denominator is `|ND|`, not `n` — §4.1.1's "proportion of supported points **therein**" refers
    back to "non-dominated solutions", distinct from `nd_n`'s "among the sample" (Design
    decisions).

    A point is supported iff it lies on a facet of the convex hull whose outward normal is
    entirely <= 0 (the minimizing-direction facet) — not merely on the hull at all, since a facet
    can face away from the minimizing orthant. If `|ND| <= M`, every non-dominated solution is
    supported by construction (too few points to span a dominating simplex) — `ConvexHull` is
    skipped.

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).
        ranking: The sample's non-dominated ranking.

    Returns:
        |supported| / |ND|. Falls back to 1.0 on `QhullError` (a coplanar/rank-deficient ND set
        with `|ND| > M`) — a **documented approximation**, not exact, expected to be practically
        unreachable for continuous, LHS-sampled objectives (Design decisions).
    """
    nondominated = ranking.nondominated
    number_of_objectives = objectives.shape[1]
    if nondominated.size <= number_of_objectives:
        return 1.0

    try:
        hull = ConvexHull(objectives[nondominated])
    except QhullError:
        return 1.0

    minimizing_facets = np.all(hull.equations[:, :-1] <= _SUPPORTED_FACET_TOLERANCE, axis=1)
    supported = np.unique(hull.simplices[minimizing_facets])
    return supported.size / nondominated.size
