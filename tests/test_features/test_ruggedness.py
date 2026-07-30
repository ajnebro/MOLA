"""Unit tests for module mola.features.ruggedness."""

import numpy as np
import pytest

from mola.distance import Neighbourhood
from mola.dominance import local_nondominance, neighbourhood_dominance
from mola.features import (
    diff_f_cor_neig,
    diff_f_dist_x_cor_neig,
    dist_f_cor_neig,
    dist_f_dist_x_cor_neig,
    dist_x_cor_neig,
    hv_cor_neig,
    hvd_cor_neig,
    inc_cor_neig,
    inf_cor_neig,
    lnd_cor_neig,
    lsupp_cor_neig,
    nhv_cor_neig,
    sup_cor_neig,
)
from mola.hypervolume import reference_point


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


class TestSupCorNeig:
    """Unit tests for sup_cor_neig."""

    def test_should_correlate_the_per_solution_dominating_proportion(self):
        """Given the shared dominance fixture, correlates each solution's dominating proportion."""
        # Arrange: A(1,4), B(2,3), C(5,5), D(0,10), k=3 (dominating counts: [0, 0, 2, 0],
        # measure = counts/3 -- verified against scipy directly: -1/3)
        objectives = np.array([[1.0, 4.0], [2.0, 3.0], [5.0, 5.0], [0.0, 10.0]])
        indices = np.array([[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)

        # Act
        value = sup_cor_neig(dominance, neighbourhood)

        # Assert
        assert value == pytest.approx(-1.0 / 3.0)


class TestInfCorNeig:
    """Unit tests for inf_cor_neig."""

    def test_should_correlate_the_per_solution_dominated_proportion(self):
        """Given the shared dominance fixture, correlates each solution's dominated proportion."""
        # Arrange: same fixture as TestSupCorNeig (dominated counts: [1, 1, 0, 0], measure =
        # counts/3 -- verified against scipy directly: -1/3)
        objectives = np.array([[1.0, 4.0], [2.0, 3.0], [5.0, 5.0], [0.0, 10.0]])
        indices = np.array([[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)

        # Act
        value = inf_cor_neig(dominance, neighbourhood)

        # Assert
        assert value == pytest.approx(-1.0 / 3.0)


class TestIncCorNeig:
    """Unit tests for inc_cor_neig."""

    def test_should_correlate_the_per_solution_incomparable_proportion(self):
        """Given the shared dominance fixture, correlates each solution's incomparable share."""
        # Arrange: same fixture as TestSupCorNeig (incomparable counts: [2, 2, 1, 3], measure =
        # counts/3 -- verified against scipy directly: -1/3)
        objectives = np.array([[1.0, 4.0], [2.0, 3.0], [5.0, 5.0], [0.0, 10.0]])
        indices = np.array([[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)

        # Act
        value = inc_cor_neig(dominance, neighbourhood)

        # Assert
        assert value == pytest.approx(-1.0 / 3.0)


class TestDistFDistXCorNeig:
    """Unit tests for dist_f_dist_x_cor_neig."""

    def test_should_correlate_the_per_solution_ratio(self):
        """Given the shared evolvability fixture, correlates each solution's own f/x ratio."""
        # Arrange: variables 0, 3, 10; objectives (0,0), (3,4), (0,8); k=2. Per-solution ratios
        # dist_f_measure/dist_x_measure = [1.0, 1.0, 6.5/8.5] (verified against scipy: -0.5)
        variables = np.array([[0.0], [3.0], [10.0]])
        objectives = np.array([[0.0, 0.0], [3.0, 4.0], [0.0, 8.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        value = dist_f_dist_x_cor_neig(objectives, variables, neighbourhood)

        # Assert
        assert value == pytest.approx(-0.5)


class TestDiffFCorNeig:
    """Unit tests for diff_f_cor_neig."""

    def test_should_correlate_the_per_solution_mean_absolute_objective_difference(self):
        """Given the shared evolvability fixture, correlates each solution's diff_f measure."""
        # Arrange: objectives (0,0), (3,4), (0,8), k=2. Per-solution mean diff_f:
        # [3.75, 3.5, 3.75] (verified against scipy directly: -0.5)
        objectives = np.array([[0.0, 0.0], [3.0, 4.0], [0.0, 8.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        value = diff_f_cor_neig(objectives, neighbourhood)

        # Assert
        assert value == pytest.approx(-0.5)


class TestDiffFDistXCorNeig:
    """Unit tests for diff_f_dist_x_cor_neig."""

    def test_should_correlate_the_per_solution_ratio(self):
        """Given the shared evolvability fixture, correlates each solution's own diff_f/x ratio."""
        # Arrange: variables 0, 3, 10; objectives (0,0), (3,4), (0,8); k=2. Per-solution ratios
        # diff_f_measure/dist_x_measure (verified against scipy directly: -0.5)
        variables = np.array([[0.0], [3.0], [10.0]])
        objectives = np.array([[0.0, 0.0], [3.0, 4.0], [0.0, 8.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        value = diff_f_dist_x_cor_neig(objectives, variables, neighbourhood)

        # Assert
        assert value == pytest.approx(-0.5)


class TestHvCorNeig:
    """Unit tests for hv_cor_neig."""

    def test_should_correlate_the_per_solution_singleton_hypervolume(self):
        """Given the shared evolvability fixture, correlates each solution's own hypervolume."""
        # Arrange: objectives (0,0), (3,4), (0,8) -> ref=(3,8) -> hv = [24, 0, 0], k=2
        # (verified against scipy directly: -0.5)
        objectives = np.array([[0.0, 0.0], [3.0, 4.0], [0.0, 8.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        ref = reference_point(objectives)

        # Act
        value = hv_cor_neig(objectives, ref, neighbourhood)

        # Assert
        assert value == pytest.approx(-0.5)


class TestHvdCorNeig:
    """Unit tests for hvd_cor_neig."""

    def test_should_correlate_the_per_solution_mean_hypervolume_difference(self):
        """Given the shared evolvability fixture, correlates each solution's hvd measure."""
        # Arrange: same objectives as TestHvCorNeig -- per-solution mean |hv(i)-hv(j)|:
        # [24, 12, 12] (verified against scipy directly: -0.5)
        objectives = np.array([[0.0, 0.0], [3.0, 4.0], [0.0, 8.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        ref = reference_point(objectives)

        # Act
        value = hvd_cor_neig(objectives, neighbourhood, ref)

        # Assert
        assert value == pytest.approx(-0.5)


class TestNhvCorNeig:
    """Unit tests for nhv_cor_neig."""

    def test_should_correlate_the_per_solution_neighbourhood_hypervolume(self):
        """Given the nhv_avg_neig fixture, correlates each solution's neighbourhood hypervolume."""
        # Arrange: same fixture as TestNhvAvgNeig -- per-solution neighbourhood hypervolumes
        # [18, 16, 18, 18] (verified against scipy directly)
        objectives = np.array([[1.0, 4.0], [2.0, 2.0], [4.0, 1.0], [6.0, 6.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        ref = reference_point(objectives)

        # Act
        value = nhv_cor_neig(objectives, neighbourhood, ref)

        # Assert
        assert value == pytest.approx(-0.4472135954999579)


class TestLndCorNeig:
    """Unit tests for lnd_cor_neig."""

    def test_should_correlate_the_per_solution_locally_non_dominated_proportion(self):
        """Given the notch fixture, correlates each solution's locally-non-dominated share."""
        # Arrange: R(10,10) dominated by everyone; A, B, D on the local hull; C(3,1.8) is a
        # "notch" (same fixture as mola.dominance's own notch test). Per-solution
        # locally-nondominated proportions [4, 3, 3, 3, 3] / 4 (verified against scipy directly)
        objectives = np.array([[10.0, 10.0], [1.0, 5.0], [2.0, 2.0], [3.0, 1.8], [5.0, 1.0]])
        indices = np.array(
            [
                [1, 2, 3, 4],
                [0, 2, 3, 4],
                [0, 1, 3, 4],
                [0, 1, 2, 4],
                [0, 1, 2, 3],
            ]
        )
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        local = local_nondominance(objectives, neighbourhood)

        # Act
        value = lnd_cor_neig(local, neighbourhood)

        # Assert
        assert value == pytest.approx(-0.25)


class TestLsuppCorNeig:
    """Unit tests for lsupp_cor_neig."""

    def test_should_correlate_the_per_solution_locally_supported_proportion(self):
        """Given the notch fixture, correlates each solution's locally-supported share."""
        # Arrange: same fixture as TestLndCorNeig -- per-solution locally-supported proportions
        # [3, 2, 2, 3, 2] / 4 (verified against scipy directly)
        objectives = np.array([[10.0, 10.0], [1.0, 5.0], [2.0, 2.0], [3.0, 1.8], [5.0, 1.0]])
        indices = np.array(
            [
                [1, 2, 3, 4],
                [0, 2, 3, 4],
                [0, 1, 3, 4],
                [0, 1, 2, 4],
                [0, 1, 2, 3],
            ]
        )
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        local = local_nondominance(objectives, neighbourhood)

        # Act
        value = lsupp_cor_neig(local, neighbourhood)

        # Assert
        assert value == pytest.approx(-0.25)
