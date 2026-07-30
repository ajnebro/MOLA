"""Unit tests for module mola.dominance."""

import numpy as np

from mola.distance import Neighbourhood
from mola.dominance import neighbourhood_dominance


class TestNeighbourhoodDominance:
    """Unit tests for neighbourhood_dominance."""

    def test_should_return_the_hand_verified_dominance_counts(self):
        """Given a small hand-verified sample, counts pairwise dominance against each neighbour."""
        # Arrange: A(1,4), B(2,3), C(5,5), D(0,10). Each solution's neighbourhood is every
        # other solution (k = n - 1 = 3). Hand-verified pairwise dominance (minimization):
        #   A dominates C (1<5, 4<5); B dominates C (2<5, 3<5).
        #   A-B, A-D, B-D, C-D are all mutually incomparable.
        objectives = np.array([[1.0, 4.0], [2.0, 3.0], [5.0, 5.0], [0.0, 10.0]])
        indices = np.array(
            [
                [1, 2, 3],  # A's neighbours: B, C, D
                [0, 2, 3],  # B's neighbours: A, C, D
                [0, 1, 3],  # C's neighbours: A, B, D
                [0, 1, 2],  # D's neighbours: A, B, C
            ]
        )
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        result = neighbourhood_dominance(objectives, neighbourhood)

        # Assert: A dominates C, is dominated by none, incomparable with B and D
        assert result.dominating[0] == 0
        assert result.dominated[0] == 1
        assert result.incomparable[0] == 2

        # Assert: B dominates C, is dominated by none, incomparable with A and D
        assert result.dominating[1] == 0
        assert result.dominated[1] == 1
        assert result.incomparable[1] == 2

        # Assert: C is dominated by A and B, dominates none, incomparable with D
        assert result.dominating[2] == 2
        assert result.dominated[2] == 0
        assert result.incomparable[2] == 1

        # Assert: D dominates none, is dominated by none, incomparable with all three
        assert result.dominating[3] == 0
        assert result.dominated[3] == 0
        assert result.incomparable[3] == 3

    def test_should_report_every_neighbour_as_incomparable_for_a_mutual_anti_chain(self):
        """Given a mutually incomparable set, every neighbour comparison is incomparable."""
        # Arrange: A(1,3), B(2,2), C(3,1) mutually incomparable, k = n - 1 = 2
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        result = neighbourhood_dominance(objectives, neighbourhood)

        # Assert
        assert np.array_equal(result.dominating, [0, 0, 0])
        assert np.array_equal(result.dominated, [0, 0, 0])
        assert np.array_equal(result.incomparable, [2, 2, 2])
