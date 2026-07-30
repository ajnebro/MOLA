"""Evolvability landscape features (paper §4.1.3, Table 1).

Evolvability features quantify the expected improvement reachable from a solution's neighbourhood
— each function here takes exactly the precomputed substrate pieces it needs, following the same
pattern as the global class.
"""

import numpy as np

from mola.distance import Neighbourhood
from mola.dominance import NeighbourhoodDominance


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
