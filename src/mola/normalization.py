"""The two whole-sample distance normalizers.

Per Design decisions ("Normalization reference"): every ``*_AVG`` distance feature is max-min
normalized against the empirical range of *all* pairwise distances in its own space, computed once
over the whole sample — never over a subset (a neighbourhood, the non-dominated pairs). Every
``*_MAX`` feature is reported raw and never touches a :class:`Normalizer`.

There are exactly two normalizers: one for decision space, one for objective space. Every feature
that normalizes a distance uses the one matching the space that distance was measured in.
"""

from dataclasses import dataclass

import numpy as np

from mola.distance import PairwiseDistanceStats, pairwise_distance_stats


@dataclass(slots=True, frozen=True)
class Normalizer:
    """A max-min range fixed once over the whole sample.

    Attributes:
        minimum: Smallest pairwise distance observed in this space.
        maximum: Largest pairwise distance observed in this space.
    """

    minimum: float
    maximum: float

    def normalize(self, value: float) -> float:
        """Max-min normalize a distance measured in this normalizer's space.

        Args:
            value: A raw distance from the same space this normalizer was built over.

        Returns:
            ``(value - minimum) / (maximum - minimum)``, or ``0.0`` when ``maximum == minimum``
            (every pairwise distance in the sample was identical, so no range exists to place
            ``value`` within) — the same degenerate-range convention jMetalPy's own
            ``util/normalization.py`` uses.
        """
        span = self.maximum - self.minimum
        if span == 0.0:
            return 0.0
        return (value - self.minimum) / span

    @classmethod
    def from_stats(cls, stats: PairwiseDistanceStats) -> "Normalizer":
        """Build a normalizer from already-computed pairwise-distance statistics.

        Args:
            stats: Statistics produced by :func:`mola.distance.pairwise_distance_stats`.

        Returns:
            A normalizer over the same range.
        """
        return cls(minimum=stats.minimum, maximum=stats.maximum)


@dataclass(slots=True, frozen=True)
class Normalizers:
    """The pair of normalizers for one sample: one per space.

    Attributes:
        variable_space: Normalizer over decision-space pairwise distances.
        objective_space: Normalizer over objective-space pairwise distances.
    """

    variable_space: Normalizer
    objective_space: Normalizer


def build_normalizers(variables: np.ndarray, objectives: np.ndarray) -> Normalizers:
    """Build both whole-sample normalizers from a sample's decision and objective vectors.

    Args:
        variables: Decision vectors, shape ``(n, D)``, with ``n >= 2``.
        objectives: Objective vectors, shape ``(n, M)``, with ``n >= 2``.

    Returns:
        The variable-space and objective-space normalizers.
    """
    return Normalizers(
        variable_space=Normalizer.from_stats(pairwise_distance_stats(variables)),
        objective_space=Normalizer.from_stats(pairwise_distance_stats(objectives)),
    )
