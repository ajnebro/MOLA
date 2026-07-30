"""The generic ruggedness procedure (paper §4.1.4).

For each of the thirteen evolvability measures, the paper computes one Spearman correlation of
that measure over every directed neighbour edge in the sample — one procedure, applied uniformly
to whichever per-solution measure is given, not thirteen bespoke implementations (Design
decisions, "Ruggedness's per-measure correlation procedure"). The two correlated arrays are built
from one shared edge loop below and cannot disagree in length by construction, so no length check
is ever needed.
"""

import numpy as np
from scipy.stats import spearmanr

from mola.distance import Neighbourhood


def neighbour_correlation(measure: np.ndarray, neighbourhood: Neighbourhood) -> float:
    """Spearman correlation of a per-solution measure over every directed neighbour edge.

    For every edge ``(i, j)`` with ``j`` a neighbour of ``i``, pairs ``(measure[i], measure[j])``
    into two parallel arrays, then one Spearman correlation over the whole edge set.

    Args:
        measure: A per-solution scalar, shape ``(n,)`` — e.g.
            ``mola.distance.neighbour_distances(variables, neighbourhood).mean(axis=1)`` for
            `dist_x_cor_neig`.
        neighbourhood: The sample's neighbourhood graph, built over the same solutions `measure`
            is indexed by.

    Returns:
        The Spearman correlation over all directed neighbour edges. NaN if `measure` is constant
        (zero variance), propagated from `scipy.stats.spearmanr` rather than special-cased.
    """
    reference_values = np.repeat(measure, neighbourhood.size)
    neighbour_values = measure[neighbourhood.indices.ravel()]
    return float(spearmanr(reference_values, neighbour_values).statistic)
