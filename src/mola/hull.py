"""The "supported" convex-hull facet test (paper §4.1.1, Ehrgott [10]).

A point is supported iff it lies on a facet of its set's convex hull whose outward normal is
entirely <= 0 (the minimizing-direction facet) — findable by minimizing some linear
scalarization. Shared by `supp_n` (global, over the whole non-dominated subset) and
`lsupp_avg_neig` (local, over each solution's own local non-dominated subset) rather than each
reimplementing the same geometry.
"""

import numpy as np
from scipy.spatial import ConvexHull, QhullError

_FACET_TOLERANCE = 1e-9
"""Floating-point slack for the "outward normal entirely <= 0" facet test."""


def supported_mask(objectives: np.ndarray) -> np.ndarray:
    """Per-point mask of which points are "supported" (Design decisions, `supp_n`).

    If there are at most `M` points (`M` = number of objectives), every point is supported by
    construction — too few points to span a dominating simplex — and `ConvexHull` is skipped.
    Falls back to "every point supported" on `QhullError` (a coplanar/rank-deficient set with
    more than `M` points) — a **documented approximation**, not exact, expected to be
    practically unreachable for continuous, LHS-sampled objectives.

    Args:
        objectives: Objective vectors in minimization form, shape (n, M). Callers are
            responsible for restricting this to a mutually non-dominated set beforehand — this
            function does not check.

    Returns:
        Boolean mask, shape (n,): True where the point lies on a minimizing-direction facet of
        the convex hull.
    """
    count, number_of_objectives = objectives.shape
    if count <= number_of_objectives:
        return np.ones(count, dtype=bool)

    try:
        hull = ConvexHull(objectives)
    except QhullError:
        return np.ones(count, dtype=bool)

    minimizing_facets = np.all(hull.equations[:, :-1] <= _FACET_TOLERANCE, axis=1)
    mask = np.zeros(count, dtype=bool)
    mask[np.unique(hull.simplices[minimizing_facets])] = True
    return mask
