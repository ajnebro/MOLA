"""Multimodality landscape features (paper §4.1.2, Table 1).

A Pareto local optimum (plo) is a sampled solution with no dominating neighbour — reuses the same
per-solution dominating-neighbour count already computed for evolvability's `sup_avg_neig`, no new
dominance machinery.
"""

import numpy as np

from mola.distance import Neighbourhood, pairwise_distance_stats
from mola.dominance import NeighbourhoodDominance
from mola.features.global_ import nd_n
from mola.multimodality import single_objective_local_optima
from mola.normalization import Normalizer
from mola.ranking import Ranking


def plo_n(dominance: NeighbourhoodDominance) -> float:
    """Proportion of Pareto local optima (Table 1: plo_n).

    A solution is a Pareto local optimum iff none of its neighbours dominates it — Design
    decisions, "Multimodality": `plo = (sup_count == 0)`.

    Args:
        dominance: Per-solution neighbour-dominance counts.

    Returns:
        |PLO| / n. Always positive: every non-dominated solution is trivially also a PLO, and a
        sample always has at least one non-dominated solution.
    """
    return float(np.mean(dominance.dominating == 0))


def plo_dist_avg(
    variables: np.ndarray, dominance: NeighbourhoodDominance, normalizer: Normalizer
) -> float:
    """Average pairwise distance among Pareto local optima in variable space (Table 1).

    Normalized against the whole sample's own variable-space distance range, like every other
    `*_AVG` distance feature (Design decisions, "Normalization reference").

    Args:
        variables: Decision vectors, shape (n, D).
        dominance: Per-solution neighbour-dominance counts, built from these same `variables`'
            neighbourhood.
        normalizer: The variable-space normalizer for this sample.

    Returns:
        The normalized average pairwise distance among PLO solutions, or NaN if fewer than 2
        solutions are PLO (too few to form a pair — possible in principle, though `plo_n`'s own
        lower bound makes it very unlikely at the paper's sampling rate).
    """
    plo = variables[dominance.dominating == 0]
    if plo.shape[0] < 2:
        return float("nan")
    return normalizer.normalize(pairwise_distance_stats(plo).mean)


def plo_dist_max(variables: np.ndarray, dominance: NeighbourhoodDominance) -> float:
    """Maximum pairwise distance among Pareto local optima in variable space (Table 1).

    Reported raw, not normalized — every `*_MAX` feature stays raw (Design decisions,
    "Normalization reference").

    Args:
        variables: Decision vectors, shape (n, D).
        dominance: Per-solution neighbour-dominance counts, built from these same `variables`'
            neighbourhood.

    Returns:
        The raw maximum pairwise distance among PLO solutions, or NaN if fewer than 2 solutions
        are PLO (see `plo_dist_avg`).
    """
    plo = variables[dominance.dominating == 0]
    if plo.shape[0] < 2:
        return float("nan")
    return pairwise_distance_stats(plo).maximum


def nd_per_plo(ranking: Ranking, dominance: NeighbourhoodDominance) -> float:
    """Non-dominated solutions per Pareto local optimum (Table 1: nd_per_plo = nd_n / plo_n).

    Args:
        ranking: The sample's non-dominated ranking.
        dominance: Per-solution neighbour-dominance counts, over the same sample as `ranking`.

    Returns:
        nd_n / plo_n. Always well-defined: `plo_n` is always positive.
    """
    return nd_n(ranking) / plo_n(dominance)


def slo_n(objectives: np.ndarray, neighbourhood: Neighbourhood) -> float:
    """Proportion of single-objective local optima per objective (Table 1: slo_n).

    A solution is a single-objective local optimum for objective `m` iff none of its neighbours
    improves `f_m` (Design decisions, "Multimodality"). Averaged over objectives: since
    `mask.mean()` over the whole `(n, M)` array is exactly the mean, over `m`, of `|S_m| / n`,
    no explicit per-objective loop is needed.

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).
        neighbourhood: The sample's neighbourhood graph.

    Returns:
        The mean, over objectives, of the proportion of solutions that are a local optimum for
        that objective. Always positive: each objective's own sample-wide minimum is trivially a
        local optimum for it.
    """
    return float(single_objective_local_optima(objectives, neighbourhood).mean())


def slo_dist_avg(
    variables: np.ndarray,
    objectives: np.ndarray,
    neighbourhood: Neighbourhood,
    normalizer: Normalizer,
) -> float:
    """Average pairwise distance among single-objective local optima (Table 1: slo_dist_avg).

    **Judgment call** (Design decisions): Table 1 doesn't restate "per objective" for this row,
    but introduces no alternative aggregation either — applies the same per-objective-then-mean-
    across-M pattern as `slo_n`. Objectives with fewer than 2 local optima (no pair to measure)
    are skipped via `nanmean` rather than blanking the whole feature.

    Args:
        variables: Decision vectors, shape (n, D).
        objectives: Objective vectors in minimization form, shape (n, M).
        neighbourhood: The sample's neighbourhood graph, built from these same `variables`.
        normalizer: The variable-space normalizer for this sample.

    Returns:
        The mean, over objectives with at least 2 local optima, of the normalized average
        pairwise distance among that objective's local optima. NaN if every objective has fewer
        than 2.
    """
    mask = single_objective_local_optima(objectives, neighbourhood)
    per_objective = np.full(objectives.shape[1], np.nan)
    for m in range(objectives.shape[1]):
        subset = variables[mask[:, m]]
        if subset.shape[0] >= 2:
            per_objective[m] = normalizer.normalize(pairwise_distance_stats(subset).mean)
    return float(np.nanmean(per_objective))


def slo_dist_max(
    variables: np.ndarray, objectives: np.ndarray, neighbourhood: Neighbourhood
) -> float:
    """Maximum pairwise distance among single-objective local optima (Table 1: slo_dist_max).

    Reported raw, not normalized, per objective — every `*_MAX` feature stays raw (Design
    decisions, "Normalization reference") — then averaged across objectives with at least 2
    local optima, same as `slo_dist_avg`.

    Args:
        variables: Decision vectors, shape (n, D).
        objectives: Objective vectors in minimization form, shape (n, M).
        neighbourhood: The sample's neighbourhood graph, built from these same `variables`.

    Returns:
        The mean, over objectives with at least 2 local optima, of the raw maximum pairwise
        distance among that objective's local optima. NaN if every objective has fewer than 2.
    """
    mask = single_objective_local_optima(objectives, neighbourhood)
    per_objective = np.full(objectives.shape[1], np.nan)
    for m in range(objectives.shape[1]):
        subset = variables[mask[:, m]]
        if subset.shape[0] >= 2:
            per_objective[m] = pairwise_distance_stats(subset).maximum
    return float(np.nanmean(per_objective))
