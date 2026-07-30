"""Single-objective local optima (paper §4.1.2).

A single-objective local optimum (slo) is a sampled solution with no neighbour that improves a
*given* objective — inherently per-objective, unlike a Pareto local optimum (plo, which reuses
`mola.dominance`'s dominating-neighbour count directly and needs no substrate of its own).
"""

import numpy as np

from mola.distance import Neighbourhood


def single_objective_local_optima(
    objectives: np.ndarray, neighbourhood: Neighbourhood
) -> np.ndarray:
    """Per-solution, per-objective single-objective-local-optimum mask.

    Solution `i` is a local optimum for objective `m` iff none of its neighbours has a strictly
    smaller `f_m` (Design decisions, "Multimodality").

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).
        neighbourhood: The sample's neighbourhood graph.

    Returns:
        Boolean mask, shape (n, M): True where solution `i` is a local optimum for objective `m`.
    """
    neighbour_values = objectives[neighbourhood.indices]
    reference_values = objectives[:, None, :]
    return (neighbour_values >= reference_values).all(axis=1)
