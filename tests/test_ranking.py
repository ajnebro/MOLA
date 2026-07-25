"""Unit tests for module mola.ranking."""

import numpy as np
import pytest

from mola.ranking import rank_solutions


class TestRankSolutions:
    """Unit tests for rank_solutions."""

    def test_should_split_into_two_hand_computed_fronts(self):
        """Given 4 incomparable trade-offs and 1 dominated solution, splits into 2 fronts."""
        # Arrange: A, B, C, D are pairwise incomparable trade-offs on 2 objectives (both
        # minimized); E is dominated by all four of them. Front 0 = {A, B, C, D}, front 1 = {E}.
        objectives = np.array(
            [
                [1.0, 4.0],  # A
                [2.0, 3.0],  # B
                [3.0, 2.0],  # C
                [4.0, 1.0],  # D
                [5.0, 5.0],  # E
            ]
        )

        # Act
        ranking = rank_solutions(objectives)

        # Assert
        np.testing.assert_array_equal(ranking.rank, [0, 0, 0, 0, 1])
        assert ranking.number_of_fronts == 2
        np.testing.assert_array_equal(sorted(ranking.fronts[0]), [0, 1, 2, 3])
        np.testing.assert_array_equal(ranking.fronts[1], [4])
        np.testing.assert_array_equal(sorted(ranking.nondominated), [0, 1, 2, 3])

    def test_should_rank_a_single_solution_as_nondominated(self):
        """Given one solution, ranks it into front 0."""
        # Arrange
        objectives = np.array([[1.0, 1.0]])

        # Act
        ranking = rank_solutions(objectives)

        # Assert
        np.testing.assert_array_equal(ranking.rank, [0])
        assert ranking.number_of_fronts == 1

    def test_should_assign_every_solution_to_exactly_one_front(self):
        """Given a random sample, every solution appears in exactly one front."""
        # Arrange
        rng = np.random.default_rng(seed=2)
        objectives = rng.uniform(size=(20, 3))

        # Act
        ranking = rank_solutions(objectives)

        # Assert
        assert sum(len(front) for front in ranking.fronts) == objectives.shape[0]
        assert len(set().union(*(set(front.tolist()) for front in ranking.fronts))) == 20

    def test_should_raise_error_on_empty_sample(self):
        """Given zero solutions, raises ValueError."""
        # Arrange
        objectives = np.zeros((0, 2))

        # Act & Assert
        with pytest.raises(ValueError, match="empty"):
            rank_solutions(objectives)
