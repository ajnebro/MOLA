"""Ruggedness landscape features (paper §4.1.4, Table 1).

Each of the thirteen evolvability measures gets a ruggedness sibling: the Spearman correlation of
that same per-solution measure over every directed neighbour edge (`mola.ruggedness`'s generic
procedure, §4.1.4) — "the larger the correlation, the smoother the landscape."
"""

import numpy as np

from mola.distance import Neighbourhood, neighbour_diff_f, neighbour_distances
from mola.dominance import NeighbourhoodDominance
from mola.hypervolume import neighbour_hypervolume_difference, singleton_hypervolume
from mola.ruggedness import neighbour_correlation


def dist_x_cor_neig(variables: np.ndarray, neighbourhood: Neighbourhood) -> float:
    """Neighbour's correlation of the average distance from neighbours in variable space.

    Args:
        variables: Decision vectors, shape (n, D).
        neighbourhood: The sample's neighbourhood graph, built from these same `variables`.

    Returns:
        The Spearman correlation, over every directed neighbour edge, of each solution's average
        distance to its own neighbours (`mola.features.evolvability.dist_x_avg_neig`'s
        per-solution measure, before the final sample-wide mean).
    """
    measure = neighbour_distances(variables, neighbourhood).mean(axis=1)
    return neighbour_correlation(measure, neighbourhood)


def dist_f_cor_neig(objectives: np.ndarray, neighbourhood: Neighbourhood) -> float:
    """Neighbour's correlation of the average distance from neighbours in objective space.

    Args:
        objectives: Objective vectors, shape (n, M).
        neighbourhood: The sample's neighbourhood graph.

    Returns:
        The Spearman correlation, over every directed neighbour edge, of each solution's average
        distance to its own neighbours in objective space
        (`mola.features.evolvability.dist_f_avg_neig`'s per-solution measure, before the final
        sample-wide mean).
    """
    measure = neighbour_distances(objectives, neighbourhood).mean(axis=1)
    return neighbour_correlation(measure, neighbourhood)


def sup_cor_neig(dominance: NeighbourhoodDominance, neighbourhood: Neighbourhood) -> float:
    """Neighbour's correlation of the proportion of dominating neighbours.

    Args:
        dominance: Per-solution neighbour-dominance counts, built from this same `neighbourhood`.
        neighbourhood: The sample's neighbourhood graph.

    Returns:
        The Spearman correlation, over every directed neighbour edge, of each solution's
        proportion of dominating neighbours (`mola.features.evolvability.sup_avg_neig`'s
        per-solution measure).
    """
    measure = dominance.dominating / neighbourhood.size
    return neighbour_correlation(measure, neighbourhood)


def inf_cor_neig(dominance: NeighbourhoodDominance, neighbourhood: Neighbourhood) -> float:
    """Neighbour's correlation of the proportion of dominated neighbours.

    Args:
        dominance: Per-solution neighbour-dominance counts, built from this same `neighbourhood`.
        neighbourhood: The sample's neighbourhood graph.

    Returns:
        The Spearman correlation, over every directed neighbour edge, of each solution's
        proportion of dominated neighbours (`mola.features.evolvability.inf_avg_neig`'s
        per-solution measure).
    """
    measure = dominance.dominated / neighbourhood.size
    return neighbour_correlation(measure, neighbourhood)


def inc_cor_neig(dominance: NeighbourhoodDominance, neighbourhood: Neighbourhood) -> float:
    """Neighbour's correlation of the proportion of incomparable neighbours.

    Args:
        dominance: Per-solution neighbour-dominance counts, built from this same `neighbourhood`.
        neighbourhood: The sample's neighbourhood graph.

    Returns:
        The Spearman correlation, over every directed neighbour edge, of each solution's
        proportion of incomparable neighbours (`mola.features.evolvability.inc_avg_neig`'s
        per-solution measure).
    """
    measure = dominance.incomparable / neighbourhood.size
    return neighbour_correlation(measure, neighbourhood)


def dist_f_dist_x_cor_neig(
    objectives: np.ndarray, variables: np.ndarray, neighbourhood: Neighbourhood
) -> float:
    """Neighbour's correlation of the ratio of average neighbour distance, objective/variable.

    Unlike `mola.features.evolvability.dist_f_dist_x_avg_neig` (a single ratio of two
    already-averaged sample-wide scalars), this ratio is computed **per solution** first, and
    only then correlated across neighbour pairs.

    Args:
        objectives: Objective vectors, shape (n, M).
        variables: Decision vectors, shape (n, D).
        neighbourhood: The sample's neighbourhood graph, built from these same `variables`.

    Returns:
        The Spearman correlation, over every directed neighbour edge, of each solution's own
        dist_f_avg_neig(i) / dist_x_avg_neig(i) ratio.
    """
    dist_f_measure = neighbour_distances(objectives, neighbourhood).mean(axis=1)
    dist_x_measure = neighbour_distances(variables, neighbourhood).mean(axis=1)
    return neighbour_correlation(dist_f_measure / dist_x_measure, neighbourhood)


def diff_f_cor_neig(objectives: np.ndarray, neighbourhood: Neighbourhood) -> float:
    """Neighbour's correlation of the average difference per objective with neighbours.

    Args:
        objectives: Objective vectors, shape (n, M).
        neighbourhood: The sample's neighbourhood graph.

    Returns:
        The Spearman correlation, over every directed neighbour edge, of each solution's average
        per-objective difference with its neighbours
        (`mola.features.evolvability.diff_f_avg_neig`'s per-solution measure).
    """
    measure = neighbour_diff_f(objectives, neighbourhood).mean(axis=1)
    return neighbour_correlation(measure, neighbourhood)


def diff_f_dist_x_cor_neig(
    objectives: np.ndarray, variables: np.ndarray, neighbourhood: Neighbourhood
) -> float:
    """Neighbour's correlation of the ratio of average objective difference to variable distance.

    Same per-solution-first-then-correlate pattern as `dist_f_dist_x_cor_neig`, with
    `diff_f_avg_neig`'s per-solution measure in place of `dist_f_avg_neig`'s.

    Args:
        objectives: Objective vectors, shape (n, M).
        variables: Decision vectors, shape (n, D).
        neighbourhood: The sample's neighbourhood graph, built from these same `variables`.

    Returns:
        The Spearman correlation, over every directed neighbour edge, of each solution's own
        diff_f_avg_neig(i) / dist_x_avg_neig(i) ratio.
    """
    diff_f_measure = neighbour_diff_f(objectives, neighbourhood).mean(axis=1)
    dist_x_measure = neighbour_distances(variables, neighbourhood).mean(axis=1)
    return neighbour_correlation(diff_f_measure / dist_x_measure, neighbourhood)


def hv_cor_neig(objectives: np.ndarray, ref: np.ndarray, neighbourhood: Neighbourhood) -> float:
    """Neighbour's correlation of the average (single) solution's hypervolume.

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).
        ref: The shared hypervolume reference point, from `mola.hypervolume.reference_point`.
        neighbourhood: The sample's neighbourhood graph.

    Returns:
        The Spearman correlation, over every directed neighbour edge, of each solution's own
        singleton hypervolume (`mola.features.evolvability.hv_avg_neig`'s per-solution measure).
    """
    measure = singleton_hypervolume(objectives, ref)
    return neighbour_correlation(measure, neighbourhood)


def hvd_cor_neig(objectives: np.ndarray, neighbourhood: Neighbourhood, ref: np.ndarray) -> float:
    """Neighbour's correlation of the average (single) solution's hypervolume difference.

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).
        neighbourhood: The sample's neighbourhood graph.
        ref: The shared hypervolume reference point, from `mola.hypervolume.reference_point`.

    Returns:
        The Spearman correlation, over every directed neighbour edge, of each solution's average
        |hv(i) - hv(j)| with its neighbours (`mola.features.evolvability.hvd_avg_neig`'s
        per-solution measure).
    """
    measure = neighbour_hypervolume_difference(objectives, neighbourhood, ref).mean(axis=1)
    return neighbour_correlation(measure, neighbourhood)
