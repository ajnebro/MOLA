"""Unit tests for module mola.distance."""

import numpy as np
import pytest

from mola.distance import build_neighbourhood, pairwise_distance_stats


class TestPairwiseDistanceStats:
    """Unit tests for pairwise_distance_stats."""

    def test_should_compute_min_max_mean_for_hand_computed_points(self):
        """Given three collinear points, computes the hand-verified min/max/mean distance."""
        # Arrange: 1-D points 0, 1, 3 -> pairwise distances 1, 3, 2
        points = np.array([[0.0], [1.0], [3.0]])

        # Act
        stats = pairwise_distance_stats(points)

        # Assert
        assert stats.minimum == pytest.approx(1.0)
        assert stats.maximum == pytest.approx(3.0)
        assert stats.mean == pytest.approx(2.0)

    def test_should_raise_error_with_fewer_than_two_points(self):
        """Given a single point, raises ValueError since no pair exists."""
        # Arrange
        points = np.zeros((1, 2))

        # Act & Assert
        with pytest.raises(ValueError, match="at least 2 points"):
            pairwise_distance_stats(points)

    @pytest.mark.parametrize("chunk_size", [1, 2, 3, 7, 512])
    def test_should_match_brute_force_regardless_of_chunk_size(self, chunk_size):
        """Given any chunk size, matches a brute-force pairwise computation."""
        # Arrange
        rng = np.random.default_rng(seed=1)
        points = rng.uniform(size=(9, 4))
        distances = [
            float(np.linalg.norm(points[i] - points[j]))
            for i in range(len(points))
            for j in range(i + 1, len(points))
        ]

        # Act
        stats = pairwise_distance_stats(points, chunk_size=chunk_size)

        # Assert
        assert stats.minimum == pytest.approx(min(distances))
        assert stats.maximum == pytest.approx(max(distances))
        assert stats.mean == pytest.approx(sum(distances) / len(distances))


class TestBuildNeighbourhood:
    """Unit tests for build_neighbourhood."""

    def test_should_return_k_nearest_neighbours_ordered_by_ascending_distance(self):
        """Given four collinear points, returns each one's two nearest neighbours closest-first."""
        # Arrange: 1-D points 0, 1, 3, 10; hand-computed nearest-2 per point
        points = np.array([[0.0], [1.0], [3.0], [10.0]])

        # Act
        neighbourhood = build_neighbourhood(points, neighbours=2)

        # Assert
        assert neighbourhood.size == 2
        np.testing.assert_array_equal(neighbourhood.indices[0], [1, 2])
        np.testing.assert_allclose(neighbourhood.distances[0], [1.0, 3.0])
        np.testing.assert_array_equal(neighbourhood.indices[1], [0, 2])
        np.testing.assert_allclose(neighbourhood.distances[1], [1.0, 2.0])
        np.testing.assert_array_equal(neighbourhood.indices[2], [1, 0])
        np.testing.assert_allclose(neighbourhood.distances[2], [2.0, 3.0])
        np.testing.assert_array_equal(neighbourhood.indices[3], [2, 1])
        np.testing.assert_allclose(neighbourhood.distances[3], [7.0, 9.0])

    def test_should_never_list_a_solution_as_its_own_neighbour(self):
        """Given a duplicate point at distance zero, still excludes the solution itself."""
        # Arrange: points 0 and 1 coincide, so solution 0's nearest "other" point is
        # at distance 0 -- exactly the case where a naive self-exclusion breaks.
        points = np.array([[0.0], [0.0], [5.0]])

        # Act
        neighbourhood = build_neighbourhood(points, neighbours=1)

        # Assert
        for solution_index, row in enumerate(neighbourhood.indices):
            assert solution_index not in row
        np.testing.assert_array_equal(neighbourhood.indices[0], [1])
        assert neighbourhood.distances[0, 0] == pytest.approx(0.0)

    def test_should_cap_neighbourhood_size_at_n_minus_1_when_sample_is_small(self):
        """Given fewer solutions than the requested neighbourhood size, caps it at n-1."""
        # Arrange
        points = np.array([[0.0], [1.0], [2.0]])

        # Act
        neighbourhood = build_neighbourhood(points, neighbours=10)

        # Assert
        assert neighbourhood.size == 2

    def test_should_raise_error_with_fewer_than_two_solutions(self):
        """Given a single solution, raises ValueError."""
        # Arrange
        points = np.zeros((1, 2))

        # Act & Assert
        with pytest.raises(ValueError, match="at least 2 solutions"):
            build_neighbourhood(points, neighbours=1)

    def test_should_raise_error_when_neighbours_is_not_positive(self):
        """Given neighbours=0, raises ValueError."""
        # Arrange
        points = np.zeros((3, 2))

        # Act & Assert
        with pytest.raises(ValueError, match="positive"):
            build_neighbourhood(points, neighbours=0)
