"""Unit tests for module mola.features.evolvability."""

import numpy as np
import pytest

from mola.distance import Neighbourhood
from mola.dominance import neighbourhood_dominance
from mola.features import inc_avg_neig, inf_avg_neig, sup_avg_neig


class TestSupAvgNeig:
    """Unit tests for sup_avg_neig."""

    def test_should_return_the_hand_verified_mean_proportion(self):
        """Given the dominance fixture from test_dominance.py, returns the mean proportion."""
        # Arrange: A(1,4), B(2,3), C(5,5), D(0,10), k=3 (dominating counts: [0, 0, 2, 0])
        objectives = np.array([[1.0, 4.0], [2.0, 3.0], [5.0, 5.0], [0.0, 10.0]])
        indices = np.array([[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)

        # Act
        value = sup_avg_neig(dominance, neighbourhood)

        # Assert: (0/3 + 0/3 + 2/3 + 0/3) / 4 = 1/6
        assert value == pytest.approx(1.0 / 6.0)

    def test_should_return_zero_for_a_mutual_anti_chain(self):
        """Given a mutually incomparable set, no neighbour ever dominates."""
        # Arrange: A(1,3), B(2,2), C(3,1) mutually incomparable, k=2
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)

        # Act
        value = sup_avg_neig(dominance, neighbourhood)

        # Assert
        assert value == pytest.approx(0.0)


class TestInfAvgNeig:
    """Unit tests for inf_avg_neig."""

    def test_should_return_the_hand_verified_mean_proportion(self):
        """Given the dominance fixture from test_dominance.py, returns the mean proportion."""
        # Arrange: A(1,4), B(2,3), C(5,5), D(0,10), k=3 (dominated counts: [1, 1, 0, 0])
        objectives = np.array([[1.0, 4.0], [2.0, 3.0], [5.0, 5.0], [0.0, 10.0]])
        indices = np.array([[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)

        # Act
        value = inf_avg_neig(dominance, neighbourhood)

        # Assert: (1/3 + 1/3 + 0/3 + 0/3) / 4 = 1/6
        assert value == pytest.approx(1.0 / 6.0)

    def test_should_return_zero_for_a_mutual_anti_chain(self):
        """Given a mutually incomparable set, no neighbour is ever dominated."""
        # Arrange: A(1,3), B(2,2), C(3,1) mutually incomparable, k=2
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)

        # Act
        value = inf_avg_neig(dominance, neighbourhood)

        # Assert
        assert value == pytest.approx(0.0)


class TestIncAvgNeig:
    """Unit tests for inc_avg_neig."""

    def test_should_return_the_hand_verified_mean_proportion(self):
        """Given the dominance fixture from test_dominance.py, returns the mean proportion."""
        # Arrange: A(1,4), B(2,3), C(5,5), D(0,10), k=3 (incomparable counts: [2, 2, 1, 3])
        objectives = np.array([[1.0, 4.0], [2.0, 3.0], [5.0, 5.0], [0.0, 10.0]])
        indices = np.array([[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)

        # Act
        value = inc_avg_neig(dominance, neighbourhood)

        # Assert: (2/3 + 2/3 + 1/3 + 3/3) / 4 = 2/3
        assert value == pytest.approx(2.0 / 3.0)

    def test_should_return_one_for_a_mutual_anti_chain(self):
        """Given a mutually incomparable set, every neighbour comparison is incomparable."""
        # Arrange: A(1,3), B(2,2), C(3,1) mutually incomparable, k=2
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)

        # Act
        value = inc_avg_neig(dominance, neighbourhood)

        # Assert
        assert value == pytest.approx(1.0)
