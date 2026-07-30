"""Unit tests for module mola.features.evolvability."""

import numpy as np
import pytest

from mola.distance import Neighbourhood
from mola.dominance import neighbourhood_dominance
from mola.features import (
    diff_f_avg_neig,
    diff_f_dist_x_avg_neig,
    dist_f_avg_neig,
    dist_f_dist_x_avg_neig,
    dist_x_avg_neig,
    hv_avg_neig,
    hvd_avg_neig,
    inc_avg_neig,
    inf_avg_neig,
    sup_avg_neig,
)
from mola.hypervolume import reference_point


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


class TestDistXAvgNeig:
    """Unit tests for dist_x_avg_neig."""

    def test_should_return_the_hand_computed_mean_neighbour_distance(self):
        """Given three 1-D points, returns the mean distance to each solution's neighbours."""
        # Arrange: points 0, 3, 10 -- everyone else is a neighbour (k=2)
        # Pairwise distances 3, 10, 7, each counted twice across the n x k matrix -> mean 20/3
        variables = np.array([[0.0], [3.0], [10.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        value = dist_x_avg_neig(variables, neighbourhood)

        # Assert
        assert value == pytest.approx(20.0 / 3.0)


class TestDistFAvgNeig:
    """Unit tests for dist_f_avg_neig."""

    def test_should_return_the_hand_computed_mean_neighbour_distance(self):
        """Given three bi-objective vectors, returns the mean distance to each's neighbours."""
        # Arrange: objectives (0,0), (3,4), (0,8) -- everyone else is a neighbour (k=2)
        # Pairwise distances 5, 8, 5, each counted twice -> mean 6.0
        objectives = np.array([[0.0, 0.0], [3.0, 4.0], [0.0, 8.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        value = dist_f_avg_neig(objectives, neighbourhood)

        # Assert
        assert value == pytest.approx(6.0)


class TestDistFDistXAvgNeig:
    """Unit tests for dist_f_dist_x_avg_neig."""

    def test_should_return_the_ratio_of_dist_f_avg_neig_to_dist_x_avg_neig(self):
        """Given the fixtures above combined, returns dist_f_avg_neig / dist_x_avg_neig."""
        # Arrange: same variables/objectives as TestDistXAvgNeig/TestDistFAvgNeig
        variables = np.array([[0.0], [3.0], [10.0]])
        objectives = np.array([[0.0, 0.0], [3.0, 4.0], [0.0, 8.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        value = dist_f_dist_x_avg_neig(objectives, variables, neighbourhood)

        # Assert: 6.0 / (20/3) = 0.9
        assert value == pytest.approx(0.9)


class TestDiffFAvgNeig:
    """Unit tests for diff_f_avg_neig."""

    def test_should_return_the_hand_computed_mean_absolute_objective_difference(self):
        """Given three bi-objective vectors, returns the mean per-objective difference."""
        # Arrange: objectives (0,0), (3,4), (0,8) -- everyone else is a neighbour (k=2)
        # Per-pair mean |diff|: A-B=3.5, A-C=4.0, B-C=3.5, each counted twice -> mean 11/3
        objectives = np.array([[0.0, 0.0], [3.0, 4.0], [0.0, 8.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        value = diff_f_avg_neig(objectives, neighbourhood)

        # Assert
        assert value == pytest.approx(11.0 / 3.0)


class TestDiffFDistXAvgNeig:
    """Unit tests for diff_f_dist_x_avg_neig."""

    def test_should_return_the_ratio_of_diff_f_avg_neig_to_dist_x_avg_neig(self):
        """Given the fixtures above combined, returns diff_f_avg_neig / dist_x_avg_neig."""
        # Arrange: same variables/objectives as TestDistXAvgNeig/TestDiffFAvgNeig
        variables = np.array([[0.0], [3.0], [10.0]])
        objectives = np.array([[0.0, 0.0], [3.0, 4.0], [0.0, 8.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        value = diff_f_dist_x_avg_neig(objectives, variables, neighbourhood)

        # Assert: (11/3) / (20/3) = 11/20 = 0.55
        assert value == pytest.approx(0.55)


class TestHvAvgNeig:
    """Unit tests for hv_avg_neig."""

    def test_should_return_the_hand_computed_mean_singleton_hypervolume(self):
        """Given three objective vectors, returns the mean per-solution box-hypervolume."""
        # Arrange: objectives (0,0), (3,4), (0,8) -> ref = (3, 8)
        # hv: A=(3-0)*(8-0)=24, B=(3-3)*(8-4)=0, C=(3-0)*(8-8)=0 -> mean 8.0
        objectives = np.array([[0.0, 0.0], [3.0, 4.0], [0.0, 8.0]])
        ref = reference_point(objectives)

        # Act
        value = hv_avg_neig(objectives, ref)

        # Assert
        assert value == pytest.approx(8.0)


class TestHvdAvgNeig:
    """Unit tests for hvd_avg_neig."""

    def test_should_return_the_hand_computed_mean_hypervolume_difference(self):
        """Given the hv_avg_neig fixture above, returns the mean |hv(i) - hv(j)| with neighbours."""
        # Arrange: same objectives as TestHvAvgNeig -- hv = [24, 0, 0], everyone else a neighbour
        # A's neighbours B, C: |24-0|=24 twice -> row mean 24
        # B's neighbours A, C: |0-24|=24, |0-0|=0 -> row mean 12
        # C's neighbours A, B: |0-24|=24, |0-0|=0 -> row mean 12
        # overall mean: (24*2 + 24 + 0 + 24 + 0) / 6 = 16.0
        objectives = np.array([[0.0, 0.0], [3.0, 4.0], [0.0, 8.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        ref = reference_point(objectives)

        # Act
        value = hvd_avg_neig(objectives, neighbourhood, ref)

        # Assert
        assert value == pytest.approx(16.0)
