"""The exact "supported" test (paper §4.1.1, Ehrgott [10]).

A non-dominated point is **supported** iff it minimizes some weighted sum of the objectives with
strictly positive weights, ties allowed (Ehrgott's supported efficient solutions). Equivalently,
by Motzkin's transposition theorem, iff no convex combination of the set's points dominates it.
Both formulations include points in the interior of a minimizing facet (supported but not
extreme) and exclude points that only a zero weight makes optimal — a plateau in one objective,
such as a constraint-violation objective sitting at zero, does not make every tied point
supported.

Shared by `supp_n` (global, over the whole non-dominated subset) and `lsupp_avg_neig` (local,
over each solution's own local non-dominated subset) rather than each reimplementing the same
geometry. Three exact methods, chosen by the number of objectives `M` for speed only — they agree
on every input, which the tests check:

* `M = 2`: the lower-left convex chain of the points sorted by the first objective.
* `M = 3, 4`: the convex hull of the points plus one unit step along every objective axis, a
  polytope whose facets through the original points are exactly those of
  ``conv(points) + R^M_>=``. A point is supported iff the outward normals of the facets it lies on
  have, between them, a negative component in every objective — the normal cone at that point
  then contains a strictly negative vector.
* `M >= 5`, or when Qhull fails: one linear program per point, maximizing the total margin by
  which a convex combination of the set dominates it.

Objectives are min-max scaled over the given set first. Supportedness is invariant under positive
per-objective scaling, so this only makes the tolerance relative to each objective's range.
"""

import numpy as np
from scipy.optimize import linprog
from scipy.spatial import ConvexHull, QhullError

_TOLERANCE = 1e-9
"""Slack, in min-max-scaled objective units, below which a margin or distance counts as zero."""

_MAX_OBJECTIVES_FOR_HULL = 4
"""Largest `M` handled by the hull method; beyond it, facet counts grow too fast and the LP wins."""


def supported_mask(objectives: np.ndarray) -> np.ndarray:
    """Per-point mask of which points are supported (Design decisions, `supp_n`).

    Args:
        objectives: Objective vectors in minimization form, shape (n, M). Callers are
            responsible for restricting this to a mutually non-dominated set beforehand — this
            function does not check. Duplicated vectors are allowed and share one verdict.

    Returns:
        Boolean mask, shape (n,): True where some strictly positive weighting of the objectives
        makes the point a minimizer over the set.
    """
    count, number_of_objectives = objectives.shape
    if count == 0:
        return np.zeros(0, dtype=bool)
    if number_of_objectives == 1:
        return np.ones(count, dtype=bool)

    scaled = _min_max_scale(objectives)
    if number_of_objectives == 2:
        return _supported_on_chain(scaled)
    if number_of_objectives <= _MAX_OBJECTIVES_FOR_HULL:
        try:
            return _supported_on_dominated_hull(scaled)
        except QhullError:
            pass
    return _supported_by_linear_programs(scaled)


def _min_max_scale(objectives: np.ndarray) -> np.ndarray:
    """Scale each objective to [0, 1] over the set; a constant objective becomes all zeros."""
    lower = objectives.min(axis=0)
    span = objectives.max(axis=0) - lower
    span[span == 0.0] = 1.0
    return (objectives - lower) / span


def _supported_on_chain(scaled: np.ndarray) -> np.ndarray:
    """Bi-objective case: a point is supported iff it lies on the lower-left convex chain.

    In a mutually non-dominated bi-objective set, sorting by the first objective sorts the second
    in decreasing order, so every edge of the lower convex hull has a negative, finite slope and
    its normal is a strictly positive weight vector. Points on an edge's interior are supported
    through that edge's weights; points above the chain are not supported by any weighting.
    """
    order = np.lexsort((scaled[:, 1], scaled[:, 0]))
    chain: list[np.ndarray] = []
    for point in scaled[order]:
        while len(chain) >= 2:
            first, second = chain[-2], chain[-1]
            cross = (second[0] - first[0]) * (point[1] - first[1]) - (second[1] - first[1]) * (
                point[0] - first[0]
            )
            if cross > 0.0:
                break
            chain.pop()
        chain.append(point)

    vertices = np.array(chain)
    chain_height = np.interp(scaled[:, 0], vertices[:, 0], vertices[:, 1])
    return scaled[:, 1] - chain_height <= _TOLERANCE


def _supported_on_dominated_hull(scaled: np.ndarray) -> np.ndarray:
    """Facet-normal test on the hull of the points and their unit steps along every axis.

    Raises:
        QhullError: If Qhull cannot build the hull; the caller falls back to linear programs.
    """
    number_of_objectives = scaled.shape[1]
    steps = [scaled + axis for axis in np.eye(number_of_objectives)]
    hull = ConvexHull(np.vstack([scaled, *steps]))
    normals, offsets = hull.equations[:, :-1], hull.equations[:, -1]

    on_facet = np.abs(scaled @ normals.T + offsets) <= _TOLERANCE
    negative_component = normals < -_TOLERANCE
    covered = on_facet.astype(np.int64) @ negative_component.astype(np.int64) > 0
    return covered.all(axis=1)


def _supported_by_linear_programs(scaled: np.ndarray) -> np.ndarray:
    """One LP per point: the largest total margin by which a convex combination dominates it.

    Minimizing ``sum_j z_j * sum_m p_jm`` over convex weights ``z`` with ``sum_j z_j p_j <= p_i``
    componentwise leaves a margin ``sum_m p_im - optimum >= 0``, zero iff nothing in the convex
    hull dominates ``p_i``. The program is always feasible (``z = e_i``) and bounded.
    """
    count = scaled.shape[0]
    row_sums = scaled.sum(axis=1)
    convexity = np.ones((1, count))
    mask = np.zeros(count, dtype=bool)
    for index in range(count):
        result = linprog(
            row_sums,
            A_ub=scaled.T,
            b_ub=scaled[index],
            A_eq=convexity,
            b_eq=[1.0],
            bounds=(0.0, None),
            method="highs",
        )
        mask[index] = row_sums[index] - result.fun <= _TOLERANCE
    return mask
