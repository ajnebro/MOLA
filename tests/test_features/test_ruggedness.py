"""Unit tests for module mola.features.ruggedness."""

import numpy as np
import pytest

from mola.distance import Neighbourhood
from mola.features import dist_f_cor_neig, dist_x_cor_neig


class TestDistXCorNeig:
    """Unit tests for dist_x_cor_neig."""

    def test_should_correlate_the_per_solution_mean_neighbour_distance(self):
        """Given the shared evolvability fixture, correlates each solution's mean distance."""
        # Arrange: points 0, 3, 10 -- everyone else is a neighbour (k=2). Per-solution mean
        # neighbour distances: [6.5, 5.0, 8.5] (verified against scipy directly: -0.5)
        variables = np.array([[0.0], [3.0], [10.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        value = dist_x_cor_neig(variables, neighbourhood)

        # Assert
        assert value == pytest.approx(-0.5)


class TestDistFCorNeig:
    """Unit tests for dist_f_cor_neig."""

    def test_should_correlate_the_per_solution_mean_neighbour_distance(self):
        """Given the shared evolvability fixture, correlates each solution's mean distance."""
        # Arrange: objectives (0,0), (3,4), (0,8) -- everyone else is a neighbour (k=2).
        # Per-solution mean neighbour distances: [6.5, 5.0, 6.5] (verified against scipy: -0.5)
        objectives = np.array([[0.0, 0.0], [3.0, 4.0], [0.0, 8.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        value = dist_f_cor_neig(objectives, neighbourhood)

        # Assert
        assert value == pytest.approx(-0.5)
