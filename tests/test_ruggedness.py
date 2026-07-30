"""Unit tests for module mola.ruggedness."""

import math

import numpy as np
import pytest

from mola.distance import Neighbourhood
from mola.ruggedness import neighbour_correlation


class TestNeighbourCorrelation:
    """Unit tests for neighbour_correlation."""

    def test_should_return_the_hand_computed_correlation_over_a_neighbour_cycle(self):
        """Given a 4-solution neighbour cycle, correlates the measure over its directed edges."""
        # Arrange: 0->1->2->3->0 (k=1 each). Edges pair (measure[i], measure[j]):
        # (1,2), (2,3), (3,4), (4,1) -- verified against scipy directly: -0.2
        measure = np.array([1.0, 2.0, 3.0, 4.0])
        indices = np.array([[1], [2], [3], [0]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        value = neighbour_correlation(measure, neighbourhood)

        # Assert
        assert value == pytest.approx(-0.2)

    def test_should_return_nan_for_a_constant_measure(self):
        """Given a measure with no variance, the correlation is undefined."""
        # Arrange: same neighbour cycle as above, but every solution has the same measure
        measure = np.array([5.0, 5.0, 5.0, 5.0])
        indices = np.array([[1], [2], [3], [0]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        value = neighbour_correlation(measure, neighbourhood)

        # Assert
        assert math.isnan(value)
