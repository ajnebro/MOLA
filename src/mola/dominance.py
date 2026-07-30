"""Pairwise and local-neighbourhood dominance.

Two related but distinct notions:

* **Pairwise** dominance (`neighbourhood_dominance`) — a thin wrapper over jMetalPy's
  `DominanceComparator.dominance_test`, applied between a reference solution and each of its
  neighbours individually — deliberately **not** a comparison of global non-dominated ranks. The
  two are not equivalent: two solutions can sit in different global fronts without either
  directly dominating the other, since front assignment reflects the whole sample's structure,
  not just the pair in question. MOORPHOLOGY's `averageProportionOfDominatingNeighbours` and its
  two siblings compare global ranks instead — a bug found by reading its source directly while
  building this module (see `CLAUDE.md`'s Audit section), not inherited here.
* **Local** non-dominance (`local_nondominance`) — whether a neighbour is non-dominated, and
  separately "supported" (`mola.hull.supported_mask`), *within the local group* `{i} ∪ N(i)`
  rather than the whole sample — the local analogue of the global `nd_n`/`supp_n` pair (Design
  decisions, "lnd/lsupp").
"""

from dataclasses import dataclass

import numpy as np
from jmetal.util.comparator import DominanceComparator

from mola.distance import Neighbourhood
from mola.hull import supported_mask
from mola.ranking import rank_solutions


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


@dataclass(slots=True, frozen=True)
class LocalNondominance:
    """Per-solution counts of locally non-dominated and locally supported neighbours.

    Attributes:
        locally_nondominated: Number of neighbours that are non-dominated within the local group
            `{i} ∪ N(i)`, shape (n,).
        locally_supported: Number of those locally non-dominated neighbours that are also
            "supported" within that local non-dominated subset, shape (n,). Always
            `<= locally_nondominated`.
    """

    locally_nondominated: np.ndarray
    locally_supported: np.ndarray


def local_nondominance(objectives: np.ndarray, neighbourhood: Neighbourhood) -> LocalNondominance:
    """Rank each solution's local group and test which neighbours are non-dominated within it.

    For each solution `i`, ranks `{i} ∪ N(i)` — via the same non-dominated sorting as the global
    `Ranking`, just restricted to this local group — and counts how many of `i`'s neighbours (not
    `i` itself) land in that local front 0 (`lnd`). Of those, further counts how many are also
    "supported" within the local non-dominated subset, via the same convex-hull facet test as the
    global `supp_n` (`lsupp`) — **not** MOORPHOLOGY's relative rank-position comparison, which
    never applied the "supported" (convex-hull) concept to `lsupp` at all despite the shared
    terminology with `supp_n` (Design decisions, "lnd/lsupp").

    Args:
        objectives: Objective vectors in minimization form, shape (n, M).
        neighbourhood: The sample's neighbourhood graph, built over these same solutions.

    Returns:
        Per-solution locally-non-dominated and locally-supported neighbour counts.
    """
    count = neighbourhood.indices.shape[0]
    locally_nondominated = np.zeros(count, dtype=int)
    locally_supported = np.zeros(count, dtype=int)

    for i in range(count):
        local_indices = np.concatenate(([i], neighbourhood.indices[i]))
        local_rank = rank_solutions(objectives[local_indices]).rank
        is_locally_nondominated = local_rank == 0
        locally_nondominated[i] = is_locally_nondominated[1:].sum()

        local_nd_positions = np.flatnonzero(is_locally_nondominated)
        supported = supported_mask(objectives[local_indices[local_nd_positions]])
        locally_supported[i] = supported[local_nd_positions != 0].sum()

    return LocalNondominance(
        locally_nondominated=locally_nondominated, locally_supported=locally_supported
    )
