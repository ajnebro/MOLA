"""Evolvability landscape features (paper §4.1.3, Table 1).

Evolvability features quantify the expected improvement reachable from a solution's neighbourhood
— each function here takes exactly the precomputed substrate pieces it needs, following the same
pattern as the global class.
"""

import numpy as np

from mola.distance import Neighbourhood, neighbour_diff_f, neighbour_distances
from mola.dominance import LocalNondominance, NeighbourhoodDominance
from mola.hypervolume import (
    neighbour_hypervolume_difference,
    neighbourhood_hypervolume,
    singleton_hypervolume,
)


def sup_avg_neig(dominance: NeighbourhoodDominance, neighbourhood: Neighbourhood) -> float:
    """Average proportion of dominating neighbours (Table 1: sup_avg_neig).

    Args:
        dominance: Per-solution neighbour-dominance counts, built from this same `neighbourhood`.
        neighbourhood: The sample's neighbourhood graph. Only `.size` is used, as the
            proportion's denominator — always the actual neighbourhood size, never a
            requested-but-possibly-capped `k` (Design decisions, "Neighbourhood definition").

    Returns:
        The mean, over the sample, of each solution's proportion of dominating neighbours.
    """
    return float(np.mean(dominance.dominating / neighbourhood.size))


def inf_avg_neig(dominance: NeighbourhoodDominance, neighbourhood: Neighbourhood) -> float:
    """Average proportion of dominated neighbours (Table 1: inf_avg_neig).

    Args:
        dominance: Per-solution neighbour-dominance counts, built from this same `neighbourhood`.
        neighbourhood: The sample's neighbourhood graph. Only `.size` is used, as the
            proportion's denominator — always the actual neighbourhood size, never a
            requested-but-possibly-capped `k` (Design decisions, "Neighbourhood definition").

    Returns:
        The mean, over the sample, of each solution's proportion of dominated neighbours.
    """
    return float(np.mean(dominance.dominated / neighbourhood.size))


def inc_avg_neig(dominance: NeighbourhoodDominance, neighbourhood: Neighbourhood) -> float:
    """Average proportion of incomparable neighbours (Table 1: inc_avg_neig).

    Args:
        dominance: Per-solution neighbour-dominance counts, built from this same `neighbourhood`.
        neighbourhood: The sample's neighbourhood graph. Only `.size` is used, as the
            proportion's denominator — always the actual neighbourhood size, never a
            requested-but-possibly-capped `k` (Design decisions, "Neighbourhood definition").

    Returns:
        The mean, over the sample, of each solution's proportion of incomparable neighbours.
    """
    return float(np.mean(dominance.incomparable / neighbourhood.size))


def lnd_avg_neig(local: LocalNondominance, neighbourhood: Neighbourhood) -> float:
    """Average proportion of locally non-dominated neighbours (Table 1: lnd_avg_neig).

    The local analogue of the global `nd_n`: a neighbour is "locally non-dominated" iff it is
    non-dominated within the local group `{i} ∪ N(i)`, not the whole sample (Design decisions,
    "lnd/lsupp") — **not** MOORPHOLOGY's comparison of the neighbour's local rank against the
    reference's own rank.

    Args:
        local: Per-solution locally-non-dominated and locally-supported neighbour counts, built
            from this same `neighbourhood`.
        neighbourhood: The sample's neighbourhood graph. Only `.size` is used, as the
            proportion's denominator.

    Returns:
        The mean, over the sample, of each solution's proportion of locally non-dominated
        neighbours.
    """
    return float(np.mean(local.locally_nondominated / neighbourhood.size))


def lsupp_avg_neig(local: LocalNondominance, neighbourhood: Neighbourhood) -> float:
    """Average proportion of supported locally non-dominated neighbours (Table 1).

    The local analogue of the global `supp_n`: among a solution's locally non-dominated
    neighbours, the proportion that are also "supported" — on a minimizing-direction facet of
    the local non-dominated subset's convex hull (`mola.hull.supported_mask`), the identical test
    `supp_n` applies globally. MOORPHOLOGY's equivalent never applied this convex-hull concept to
    `lsupp` at all, despite sharing supp_n's "supported" terminology (Design decisions).

    Args:
        local: Per-solution locally-non-dominated and locally-supported neighbour counts, built
            from this same `neighbourhood`.
        neighbourhood: The sample's neighbourhood graph. Only `.size` is used, as the
            proportion's denominator — matching `lnd_avg_neig`'s convention, not
            `supp_n`'s `|ND|` denominator (Table 1: "proportion... of neighbours", not "...
            therein").

    Returns:
        The mean, over the sample, of each solution's proportion of supported locally
        non-dominated neighbours.
    """
    return float(np.mean(local.locally_supported / neighbourhood.size))


def dist_x_avg_neig(variables: np.ndarray, neighbourhood: Neighbourhood) -> float:
    """Average distance from each solution to its neighbours in variable space (Table 1).

    Args:
        variables: Decision vectors, shape (n, D).
        neighbourhood: The sample's neighbourhood graph, built from these same `variables`.

    Returns:
        The mean, over the sample, of each solution's average distance to its neighbours.
    """
    return float(neighbour_distances(variables, neighbourhood).mean())


def dist_f_avg_neig(objectives: np.ndarray, neighbourhood: Neighbourhood) -> float:
    """Average distance from each solution to its neighbours in objective space (Table 1).

    Args:
        objectives: Objective vectors, shape (n, M).
        neighbourhood: The sample's neighbourhood graph (built in decision space; only the
            neighbour *relation* is reused here — distances are measured in objective space).

    Returns:
        The mean, over the sample, of each solution's average distance to its neighbours.
    """
    return float(neighbour_distances(objectives, neighbourhood).mean())


def dist_f_dist_x_avg_neig(
    objectives: np.ndarray, variables: np.ndarray, neighbourhood: Neighbourhood
) -> float:
    """Ratio of dist_f_avg_neig to dist_x_avg_neig (Table 1's own parenthetical formula).

    Args:
        objectives: Objective vectors, shape (n, M).
        variables: Decision vectors, shape (n, D).
        neighbourhood: The sample's neighbourhood graph, built from these same `variables`.

    Returns:
        dist_f_avg_neig / dist_x_avg_neig.
    """
    return dist_f_avg_neig(objectives, neighbourhood) / dist_x_avg_neig(variables, neighbourhood)


def diff_f_avg_neig(objectives: np.ndarray, neighbourhood: Neighbourhood) -> float:
    """Average difference per objective with neighbours (Table 1: diff_f_avg_neig).

    Unsigned — the mean absolute per-objective difference, not signed — matching every other
    averaged distance-like feature in this family, since the neighbour relation is directional
    (`j` in `N(i)` doesn't imply `i` in `N(j)`) and a signed average could cancel out real
    structure (Design decisions).

    Args:
        objectives: Objective vectors, shape (n, M).
        neighbourhood: The sample's neighbourhood graph.

    Returns:
        The mean, over the sample, of each solution's average per-objective difference with its
        neighbours.
    """
    return float(neighbour_diff_f(objectives, neighbourhood).mean())


def diff_f_dist_x_avg_neig(
    objectives: np.ndarray, variables: np.ndarray, neighbourhood: Neighbourhood
) -> float:
    """Ratio of diff_f_avg_neig to dist_x_avg_neig (Table 1's own parenthetical formula).

    Args:
        objectives: Objective vectors, shape (n, M).
        variables: Decision vectors, shape (n, D).
        neighbourhood: The sample's neighbourhood graph, built from these same `variables`.

    Returns:
        diff_f_avg_neig / dist_x_avg_neig.
    """
    return diff_f_avg_neig(objectives, neighbourhood) / dist_x_avg_neig(variables, neighbourhood)


def hv_avg_neig(objectives: np.ndarray, ref: np.ndarray) -> float:
    """Average (single) solution's hypervolume (Table 1: hv_avg_neig).

    The "(single)" qualifier is load-bearing: each solution is scored in isolation against the
    shared reference point, not `moocore.hv_contributions` (Design decisions,
    `mola.hypervolume.singleton_hypervolume`).

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).
        ref: The shared hypervolume reference point, from `mola.hypervolume.reference_point`.

    Returns:
        The mean, over the sample, of each solution's own box-hypervolume against `ref`.
    """
    return float(singleton_hypervolume(objectives, ref).mean())


def hvd_avg_neig(objectives: np.ndarray, neighbourhood: Neighbourhood, ref: np.ndarray) -> float:
    """Average (single) solution's hypervolume difference with neighbours (Table 1: hvd_avg_neig).

    Reuses the same per-solution hypervolume array as `hv_avg_neig`: unsigned difference, same
    convention as `diff_f_avg_neig` (Design decisions).

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).
        neighbourhood: The sample's neighbourhood graph.
        ref: The shared hypervolume reference point, from `mola.hypervolume.reference_point`.

    Returns:
        The mean, over the sample, of each solution's average |hv(i) - hv(j)| with its
        neighbours.
    """
    return float(neighbour_hypervolume_difference(objectives, neighbourhood, ref).mean())


def nhv_avg_neig(objectives: np.ndarray, neighbourhood: Neighbourhood, ref: np.ndarray) -> float:
    """Average hypervolume from the whole neighbourhood (Table 1: nhv_avg_neig).

    Genuinely set-based, unlike `hv_avg_neig`'s singleton score: the joint hypervolume of each
    solution's `k` neighbours (excluding the solution itself) against the shared reference point
    (`mola.hypervolume.neighbourhood_hypervolume`, via `moocore.hypervolume`).

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).
        neighbourhood: The sample's neighbourhood graph.
        ref: The shared hypervolume reference point, from `mola.hypervolume.reference_point`.

    Returns:
        The mean, over the sample, of each solution's neighbourhood hypervolume.
    """
    return float(neighbourhood_hypervolume(objectives, neighbourhood, ref).mean())
