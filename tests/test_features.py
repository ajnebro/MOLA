"""Unit tests for module mola.features."""

import numpy as np
import pytest

from mola.features import dist_f_max, dist_x_avg, dist_x_max
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


class TestDistXMax:
    """Unit tests for dist_x_max."""

    def test_should_return_the_hand_computed_raw_maximum_pairwise_distance_1d(self):
        """Given three collinear points, returns their raw maximum pairwise distance."""
        # Arrange: 1-D points 0, 1, 3 -> pairwise distances 1, 3, 2 -> max 3
        variables = np.array([[0.0], [1.0], [3.0]])

        # Act
        value = dist_x_max(variables)

        # Assert: raw, not normalized
        assert value == pytest.approx(3.0)

    def test_should_return_the_hand_computed_raw_maximum_pairwise_distance_2d(self):
        """Given three 2-D points, returns their raw maximum pairwise distance."""
        # Arrange: pairwise distances 5, 10, 5 -> max 10
        variables = np.array([[0.0, 0.0], [3.0, 4.0], [6.0, 8.0]])

        # Act
        value = dist_x_max(variables)

        # Assert: raw, not normalized
        assert value == pytest.approx(10.0)


class TestDistFMax:
    """Unit tests for dist_f_max."""

    def test_should_return_the_hand_computed_raw_maximum_pairwise_distance_1d(self):
        """Given three single-objective vectors, returns their raw maximum pairwise distance."""
        # Arrange: objectives 2, 5, 9 -> pairwise distances 3, 7, 4 -> max 7
        objectives = np.array([[2.0], [5.0], [9.0]])

        # Act
        value = dist_f_max(objectives)

        # Assert: raw, not normalized
        assert value == pytest.approx(7.0)

    def test_should_return_the_hand_computed_raw_maximum_pairwise_distance_2d(self):
        """Given three bi-objective vectors, returns their raw maximum pairwise distance."""
        # Arrange: pairwise distances 5, 4, 3 -> max 5
        objectives = np.array([[1.0, 1.0], [4.0, 5.0], [1.0, 5.0]])

        # Act
        value = dist_f_max(objectives)

        # Assert: raw, not normalized
        assert value == pytest.approx(5.0)
