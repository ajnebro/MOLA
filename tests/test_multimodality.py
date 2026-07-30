"""Unit tests for module mola.multimodality."""

import numpy as np

from mola.distance import Neighbourhood
from mola.multimodality import single_objective_local_optima


class TestSingleObjectiveLocalOptima:
    """Unit tests for single_objective_local_optima."""

    def test_should_return_the_hand_verified_mask_over_a_fully_connected_neighbourhood(self):
        """Given four solutions and a complete neighbourhood, marks each objective's minimum."""
        # Arrange: A(1,5), B(3,2), C(2,4), D(5,1), everyone else is a neighbour (k=3).
        # A has the smallest f_1 (1) -> the only f_1 local optimum. D has the smallest f_2 (1)
        # -> the only f_2 local optimum.
        objectives = np.array([[1.0, 5.0], [3.0, 2.0], [2.0, 4.0], [5.0, 1.0]])
        indices = np.array([[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        mask = single_objective_local_optima(objectives, neighbourhood)

        # Assert
        np.testing.assert_array_equal(
            mask, [[True, False], [False, False], [False, False], [False, True]]
        )

    def test_should_allow_more_than_one_local_optimum_per_objective_across_disconnected_pairs(
        self,
    ):
        """Given two disconnected neighbour pairs, each pair can have its own f_1 local optimum."""
        # Arrange: A(1,9)-B(5,9) are mutual neighbours; C(2,9)-D(8,9) are mutual neighbours.
        # A's f_1 (1) beats its only neighbour B's (5) -> A is a local optimum.
        # C's f_1 (2) beats its only neighbour D's (8) -> C is a local optimum too, independently.
        # f_2 is constant (9) for everyone, so every solution is trivially a local optimum for it.
        objectives = np.array([[1.0, 9.0], [5.0, 9.0], [2.0, 9.0], [8.0, 9.0]])
        indices = np.array([[1], [0], [3], [2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        mask = single_objective_local_optima(objectives, neighbourhood)

        # Assert
        np.testing.assert_array_equal(
            mask, [[True, True], [False, True], [True, True], [False, True]]
        )
