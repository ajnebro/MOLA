"""Unit tests for module mola.multimodality."""

import numpy as np

from mola.distance import Neighbourhood
from mola.multimodality import adaptive_walk, adaptive_walks, single_objective_local_optima


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


# Shared five-solution chain fixture for TestAdaptiveWalk and TestAdaptiveWalks: A(0)=(10,10),
# B(1)=(5,5), C(2)=(3,3), D(3)=(1,1) form a strict dominance chain (D dominates C dominates B
# dominates A); E(4)=(20,20) is worse than everyone, so it dominates nobody. Neighbours (k=2)
# are hand-picked, in the exact order each solution should scan them.
_CHAIN_OBJECTIVES = np.array([[10.0, 10.0], [5.0, 5.0], [3.0, 3.0], [1.0, 1.0], [20.0, 20.0]])
_CHAIN_INDICES = np.array([[4, 1], [2, 0], [3, 0], [2, 1], [0, 1]])
_CHAIN_NEIGHBOURHOOD = Neighbourhood(
    indices=_CHAIN_INDICES, distances=np.zeros_like(_CHAIN_INDICES, dtype=float)
)


class TestAdaptiveWalk:
    """Unit tests for adaptive_walk."""

    def test_should_walk_uphill_through_the_dominance_chain(self):
        """Starting at the worst solution, walks through every improving step to the best."""
        # Arrange: A's neighbours are E (checked first, does not dominate A) then B (dominates
        # A, accepted) -> 2 evaluations. B->C: 1 evaluation (C dominates B, checked first).
        # C->D: 1 evaluation (D dominates C, checked first). D: neither neighbour dominates it
        # (D is the chain's best) -> 2 evaluations, walk stops.

        # Act
        walk = adaptive_walk(_CHAIN_OBJECTIVES, _CHAIN_NEIGHBOURHOOD, 0)

        # Assert: A -> B -> C -> D, 3 accepted moves, 2 + 1 + 1 + 2 = 6 evaluations
        assert walk.length == 3
        assert walk.evaluations == 6

    def test_should_return_a_zero_length_walk_when_starting_at_a_pareto_local_optimum(self):
        """Starting already at the best solution, the walk stops immediately."""
        # Arrange: D's neighbours are C and B, neither dominates D -> 2 evaluations, no move

        # Act
        walk = adaptive_walk(_CHAIN_OBJECTIVES, _CHAIN_NEIGHBOURHOOD, 3)

        # Assert
        assert walk.length == 0
        assert walk.evaluations == 2


class TestAdaptiveWalks:
    """Unit tests for adaptive_walks."""

    def test_should_return_every_hand_traced_walk_when_samples_covers_the_whole_sample(self):
        """Given samples == n, every solution is used as a starting point exactly once."""
        # Arrange: the five walks, hand-traced individually (A->D above; B->C->D: 1+1+2=4
        # evaluations, length 2; C->D: 1+2=3 evaluations, length 1; E->A->B->C->D: 1+2+1+1+2=7
        # evaluations, length 4) -- each cross-checked against adaptive_walk directly

        # Act
        walks = adaptive_walks(_CHAIN_OBJECTIVES, _CHAIN_NEIGHBOURHOOD, samples=5, seed=0)

        # Assert: every index is a starting point exactly once, so the *set* of outcomes is
        # fixed regardless of the random draw order
        assert sorted(walks.lengths.tolist()) == [0, 1, 2, 3, 4]
        assert sorted(walks.evaluations.tolist()) == [2, 3, 4, 6, 7]

    def test_should_cap_the_number_of_walks_at_the_sample_size(self):
        """Given samples > n, runs at most one walk per solution instead of raising."""
        # Act
        walks = adaptive_walks(_CHAIN_OBJECTIVES, _CHAIN_NEIGHBOURHOOD, samples=30, seed=0)

        # Assert
        assert walks.lengths.size == 5
        assert walks.evaluations.size == 5
