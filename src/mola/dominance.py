"""Pairwise dominance between each solution and its neighbours.

Thin wrapper over jMetalPy's `DominanceComparator.dominance_test`, applied between a reference
solution and each of its neighbours individually — deliberately **not** a comparison of global
non-dominated ranks. The two are not equivalent: two solutions can sit in different global fronts
without either directly dominating the other, since front assignment reflects the whole sample's
structure, not just the pair in question. MOORPHOLOGY's `averageProportionOfDominatingNeighbours`
and its two siblings compare global ranks instead — a bug found by reading its source directly
while building this module (see `CLAUDE.md`'s Audit section), not inherited here.
"""

from dataclasses import dataclass

import numpy as np
from jmetal.util.comparator import DominanceComparator

from mola.distance import Neighbourhood


@dataclass(slots=True, frozen=True)
class NeighbourhoodDominance:
    """Per-solution counts of how its neighbours compare under pairwise dominance.

    Attributes:
        dominating: Number of neighbours that dominate the reference solution, shape (n,).
        dominated: Number of neighbours dominated by the reference solution, shape (n,).
        incomparable: Number of neighbours neither dominating nor dominated, shape (n,).
    """

    dominating: np.ndarray
    dominated: np.ndarray
    incomparable: np.ndarray


def neighbourhood_dominance(
    objectives: np.ndarray, neighbourhood: Neighbourhood
) -> NeighbourhoodDominance:
    """Test each solution against each of its neighbours under pairwise dominance.

    Dominance is evaluated under minimization throughout, matching the interchange contract.

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).
        neighbourhood: The sample's neighbourhood graph, built over these same solutions.

    Returns:
        Per-solution dominating/dominated/incomparable neighbour counts.
    """
    comparator = DominanceComparator()
    count = neighbourhood.indices.shape[0]
    dominating = np.zeros(count, dtype=int)
    dominated = np.zeros(count, dtype=int)
    incomparable = np.zeros(count, dtype=int)

    for i in range(count):
        for j in neighbourhood.indices[i]:
            result = comparator.dominance_test(objectives[j], objectives[i])
            if result < 0:
                dominating[i] += 1
            elif result > 0:
                dominated[i] += 1
            else:
                incomparable[i] += 1

    return NeighbourhoodDominance(
        dominating=dominating, dominated=dominated, incomparable=incomparable
    )
