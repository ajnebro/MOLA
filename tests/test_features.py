"""Unit tests for module mola.features."""

import numpy as np
import pytest

from mola.features import dist_x_avg
from mola.normalization import Normalizer


class TestDistXAvg:
    """Unit tests for dist_x_avg."""

    def test_should_normalize_the_hand_computed_mean_pairwise_distance_1d(self):
        """Given three collinear points, normalizes their mean pairwise distance."""
        # Arrange: 1-D points 0, 1, 3 -> pairwise distances 1, 3, 2 -> mean 2, range [1, 3]
        variables = np.array([[0.0], [1.0], [3.0]])
        normalizer = Normalizer(minimum=1.0, maximum=3.0)

        # Act
        value = dist_x_avg(variables, normalizer)

        # Assert: (2 - 1) / (3 - 1) = 0.5
        assert value == pytest.approx(0.5)

    def test_should_normalize_the_hand_computed_mean_pairwise_distance_2d(self):
        """Given three 2-D points, normalizes their mean pairwise distance."""
        # Arrange: pairwise distances 5, 10, 5 -> mean 20/3, range [5, 10]
        variables = np.array([[0.0, 0.0], [3.0, 4.0], [6.0, 8.0]])
        normalizer = Normalizer(minimum=5.0, maximum=10.0)

        # Act
        value = dist_x_avg(variables, normalizer)

        # Assert: (20/3 - 5) / (10 - 5) = 1/3
        assert value == pytest.approx(1.0 / 3.0)
