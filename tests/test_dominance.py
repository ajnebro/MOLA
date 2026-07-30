"""Unit tests for module mola.dominance."""

import numpy as np

from mola.distance import Neighbourhood
from mola.dominance import local_nondominance, neighbourhood_dominance


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


class TestLocalNondominance:
    """Unit tests for local_nondominance."""

    def test_should_count_locally_non_dominated_and_supported_neighbours(self):
        """Given a reference solution whose local group has a dominated member, counts both."""
        # Arrange: A(1,5), B(2,2), C(5,1) mutually incomparable; D(3,3) dominated by B
        # (2<=3, 2<=3, strict). A's local group {A,B,C,D} ranks front0={A,B,C}, front1={D}.
        objectives = np.array([[1.0, 5.0], [2.0, 2.0], [5.0, 1.0], [3.0, 3.0], [10.0, 10.0]])
        indices = np.array(
            [
                [1, 2, 3],  # A -> B, C, D
                [0, 2, 3],  # B -> A, C, D
                [0, 1, 3],  # C -> A, B, D
                [0, 1, 2],  # D -> A, B, C
                [0, 1, 2],  # E -> unused as reference here
            ]
        )
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        result = local_nondominance(objectives, neighbourhood)

        # Assert: A's locally-nd neighbours are B and C (not D, dominated locally) -> 2;
        # the local ND subset {A, B, C} is a proper triangle -- all 3 supported, so both of A's
        # locally-nd neighbours (B, C) are also locally supported -> 2
        assert result.locally_nondominated[0] == 2
        assert result.locally_supported[0] == 2

        # Assert: D itself is locally dominated (excluded from the local ND subset entirely),
        # so all three of its neighbours (A, B, C) are locally non-dominated *and* supported
        assert result.locally_nondominated[3] == 3
        assert result.locally_supported[3] == 3

    def test_should_exclude_a_locally_non_dominated_notch_neighbour_from_the_supported_count(
        self,
    ):
        """A neighbour can be locally non-dominated yet still not locally supported."""
        # Arrange: R(10,10) dominated by everyone; A(1,5), B(2,2), D(5,1) on the local hull;
        # C(3,1.8) is a "notch" -- locally non-dominated but not on the hull (same fixture as
        # mola.hull's own notch test, embedded here as R's neighbourhood)
        objectives = np.array([[10.0, 10.0], [1.0, 5.0], [2.0, 2.0], [3.0, 1.8], [5.0, 1.0]])
        indices = np.array(
            [
                [1, 2, 3, 4],  # R -> A, B, C, D
                [0, 2, 3, 4],  # A -> unused as reference here
                [0, 1, 3, 4],
                [0, 1, 2, 4],
                [0, 1, 2, 3],
            ]
        )
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        result = local_nondominance(objectives, neighbourhood)

        # Assert: R itself is dominated by all four neighbours, so none of them are excluded
        # from the local ND subset by R's own presence -- all four (A, B, C, D) are locally
        # non-dominated, but only three (A, B, D) sit on the hull -- C, the notch, does not
        assert result.locally_nondominated[0] == 4
        assert result.locally_supported[0] == 3
