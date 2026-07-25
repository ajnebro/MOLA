"""Global landscape features (paper §4.1.1, Table 1).

Each function takes exactly the precomputed substrate pieces it needs (a normalizer, a ranking, a
neighbourhood, ...) rather than a whole Sample, so it stays testable and reasoned about in
isolation. An orchestrator that builds the shared substrate once per sample and calls every
feature belongs here once enough features exist to justify one — premature now, with a single
feature implemented.
"""

import numpy as np

from mola.distance import pairwise_distance_stats
from mola.normalization import Normalizer


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
