"""Global landscape features (paper §4.1.1, Table 1).

Each function takes exactly the precomputed substrate pieces it needs (a normalizer, a ranking, a
neighbourhood, ...) rather than a whole Sample, so it stays testable and reasoned about in
isolation. An orchestrator that builds the shared substrate once per sample and calls every
feature belongs here once enough features exist to justify one.
"""

import numpy as np

from mola.distance import pairwise_distance_stats
from mola.normalization import Normalizer
from mola.ranking import Ranking


def dist_x_avg(variables: np.ndarray, normalizer: Normalizer) -> float:
    """Average pairwise distance among sampled solutions in variable space (Table 1: dist_x_avg).

    Normalized against the whole sample's own variable-space distance range, per Design
    decisions ("Normalization reference") — `normalizer` must be built from these same
    `variables` (see `mola.normalization.build_normalizers`).

    Args:
        variables: Decision vectors, shape (n, D), with n >= 2.
        normalizer: The variable-space normalizer for this sample.

    Returns:
        The normalized average pairwise variable-space distance, in [0, 1].
    """
    return normalizer.normalize(pairwise_distance_stats(variables).mean)


def dist_x_max(variables: np.ndarray) -> float:
    """Maximum pairwise distance among sampled solutions in variable space (Table 1: dist_x_max).

    Reported raw, not normalized — every `*_MAX` feature stays raw (Design decisions,
    "Normalization reference").

    Args:
        variables: Decision vectors, shape (n, D), with n >= 2.

    Returns:
        The raw maximum pairwise variable-space distance.
    """
    return pairwise_distance_stats(variables).maximum


def dist_f_max(objectives: np.ndarray) -> float:
    """Maximum pairwise distance among sampled solutions in objective space (Table 1: dist_f_max).

    Reported raw, not normalized — every `*_MAX` feature stays raw (Design decisions,
    "Normalization reference").

    Args:
        objectives: Objective vectors, shape (n, M), with n >= 2.

    Returns:
        The raw maximum pairwise objective-space distance.
    """
    return pairwise_distance_stats(objectives).maximum


def nd_n(ranking: Ranking) -> float:
    """Proportion of non-dominated solutions among the sample (Table 1: nd_n).

    Args:
        ranking: The sample's non-dominated ranking.

    Returns:
        |non-dominated| / n, in the interval (0, 1].
    """
    return ranking.nondominated.size / ranking.rank.size


def rank_avg(ranking: Ranking) -> float:
    """Average rank with respect to non-dominated sorting (Table 1: rank_avg).

    Rank is zero-based — rank 0 is the non-dominated front — following
    `mola.ranking.rank_solutions`'s own convention.

    Args:
        ranking: The sample's non-dominated ranking.

    Returns:
        The mean per-solution rank.
    """
    return float(ranking.rank.mean())
