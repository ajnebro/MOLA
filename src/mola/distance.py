"""Pairwise-distance statistics and the neighbourhood graph.

Two pieces of the shared substrate every landscape feature builds on:

* the global empirical range of pairwise Euclidean distances over the whole sample, which anchors
  the two normalizers (see :mod:`mola.normalization`);
* the neighbourhood graph, i.e. each solution's ``k`` nearest *other* solutions in **decision**
  space, sorted from closest to furthest.

The pairwise statistics are accumulated in blocks rather than by materializing an ``n x n`` matrix:
at the paper's own sampling rate of ``n = 200 * D``, a 30-variable problem yields 6000 solutions,
whose full distance matrix would cost roughly 288 MB per space.
"""

from dataclasses import dataclass

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.distance import cdist

DEFAULT_CHUNK_SIZE = 512
"""Number of rows compared per block in :func:`pairwise_distance_stats`."""


@dataclass(slots=True, frozen=True)
class PairwiseDistanceStats:
    """Summary of the Euclidean distances over all unordered pairs of a point set.

    Attributes:
        minimum: Smallest pairwise distance.
        maximum: Largest pairwise distance.
        mean: Arithmetic mean over all ``n * (n - 1) / 2`` pairwise distances.
    """

    minimum: float
    maximum: float
    mean: float


@dataclass(slots=True, frozen=True)
class Neighbourhood:
    """Each solution's nearest other solutions in decision space.

    Row ``i`` of both arrays describes solution ``i``'s neighbours, ordered from closest to
    furthest — an order the multi-objective adaptive walk depends on, since it accepts the first
    dominating neighbour scanning outwards.

    Attributes:
        indices: Neighbour indices, shape ``(n, k)``. A solution is never its own neighbour.
        distances: Matching decision-space distances, shape ``(n, k)``, ascending along each row.
    """

    indices: np.ndarray
    distances: np.ndarray

    @property
    def size(self) -> int:
        """Number of neighbours per solution (``k``)."""
        return self.indices.shape[1]


def pairwise_distance_stats(
    points: np.ndarray, *, chunk_size: int = DEFAULT_CHUNK_SIZE
) -> PairwiseDistanceStats:
    """Summarize the Euclidean distances over every unordered pair of points.

    Args:
        points: Point set, shape ``(n, dimensions)``, with ``n >= 2``.
        chunk_size: Number of rows compared per block. Trades peak memory for loop overhead;
            it does not affect the result.

    Returns:
        The minimum, maximum and mean pairwise distance.

    Raises:
        ValueError: If fewer than two points are given, so that no pair exists.
    """
    if points.shape[0] < 2:
        raise ValueError(f"at least 2 points are needed to form a pair, got {points.shape[0]}")

    count = points.shape[0]
    minimum = np.inf
    maximum = -np.inf
    total = 0.0
    for start in range(0, count, chunk_size):
        stop = min(start + chunk_size, count)
        block = cdist(points[start:stop], points[start:])
        rows = np.arange(stop - start)[:, None]
        columns = np.arange(count - start)[None, :]
        upper_triangle = block[columns > rows]
        if upper_triangle.size > 0:
            minimum = min(minimum, float(upper_triangle.min()))
            maximum = max(maximum, float(upper_triangle.max()))
            total += float(upper_triangle.sum())

    return PairwiseDistanceStats(
        minimum=minimum,
        maximum=maximum,
        mean=total / (count * (count - 1) / 2),
    )


def build_neighbourhood(variables: np.ndarray, neighbours: int) -> Neighbourhood:
    """Build the neighbourhood graph over a sample's decision vectors.

    Each solution's neighbours are the ``k`` nearest *other* solutions by Euclidean distance in
    decision space. The self-point is excluded by index rather than by position, so duplicated
    decision vectors — which put several points at distance zero — cannot displace it and leave a
    solution listed as its own neighbour.

    Args:
        variables: Decision vectors, shape ``(n, D)``.
        neighbours: Requested neighbourhood size ``k``. Capped at ``n - 1`` when the sample is
            too small to supply that many; the resulting size is reported by
            :attr:`Neighbourhood.size`, which callers must use as the denominator of any
            neighbourhood proportion instead of assuming ``k``.

    Returns:
        The neighbourhood graph.

    Raises:
        ValueError: If fewer than two solutions are given, or if ``neighbours`` is not positive.
    """
    if variables.shape[0] < 2:
        raise ValueError(
            f"at least 2 solutions are needed to form a neighbourhood, got {variables.shape[0]}"
        )
    if neighbours < 1:
        raise ValueError(f"neighbours must be positive, got {neighbours}")

    count = variables.shape[0]
    effective = min(neighbours, count - 1)
    tree = cKDTree(variables)
    distances, indices = tree.query(variables, k=effective + 1)

    # Drop exactly one occurrence of the self index per row; when ties hide it (identical
    # decision vectors), fall back to dropping the furthest candidate.
    is_self = indices == np.arange(count)[:, None]
    dropped = np.where(is_self.any(axis=1), np.argmax(is_self, axis=1), effective)
    kept = np.arange(effective + 1)[None, :] != dropped[:, None]

    return Neighbourhood(
        indices=indices[kept].reshape(count, effective),
        distances=distances[kept].reshape(count, effective),
    )
