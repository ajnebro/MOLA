"""Ruggedness landscape features (paper §4.1.4, Table 1).

Each of the thirteen evolvability measures gets a ruggedness sibling: the Spearman correlation of
that same per-solution measure over every directed neighbour edge (`mola.ruggedness`'s generic
procedure, §4.1.4) — "the larger the correlation, the smoother the landscape."
"""

import numpy as np

from mola.distance import Neighbourhood, neighbour_distances
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
