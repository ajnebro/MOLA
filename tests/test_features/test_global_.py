"""Unit tests for module mola.features."""

import math

import numpy as np
import pytest

from mola.features import (
    dist_f_avg,
    dist_f_max,
    dist_x_avg,
    dist_x_max,
    dist_x_nd_avg,
    dist_x_nd_max,
    f_cor,
    fdc,
    nd_n,
    rank_avg,
    rank_ent,
    rank_max,
)
from mola.normalization import Normalizer
from mola.ranking import rank_solutions


class TestDistXAvg:
    """Unit tests for dist_x_avg."""

    def test_should_normalize_the_hand_computed_mean_pairwise_distance_1d(self):
        """Given three collinear points, normalizes their mean pairwise distance."""
        # Arrange: 1-D points 0, 1, 3 -> pairwise distances 1, 3, 2 -> mean 2, range [1, 3]
        variables = np.array([[0.0], [1.0], [3.0]])
        normalizer = Normalizer(minimum=1.0, maximum=3.0)

        # Act
        value = dist_x_avg(variables, normalizer)

        # Assert: (2 - 1) / (3 - 1) = 0.5
        assert value == pytest.approx(0.5)

    def test_should_normalize_the_hand_computed_mean_pairwise_distance_2d(self):
        """Given three 2-D points, normalizes their mean pairwise distance."""
        # Arrange: pairwise distances 5, 10, 5 -> mean 20/3, range [5, 10]
        variables = np.array([[0.0, 0.0], [3.0, 4.0], [6.0, 8.0]])
        normalizer = Normalizer(minimum=5.0, maximum=10.0)

        # Act
        value = dist_x_avg(variables, normalizer)

        # Assert: (20/3 - 5) / (10 - 5) = 1/3
        assert value == pytest.approx(1.0 / 3.0)


class TestDistXMax:
    """Unit tests for dist_x_max."""

    def test_should_return_the_hand_computed_raw_maximum_pairwise_distance_1d(self):
        """Given three collinear points, returns their raw maximum pairwise distance."""
        # Arrange: 1-D points 0, 1, 3 -> pairwise distances 1, 3, 2 -> max 3
        variables = np.array([[0.0], [1.0], [3.0]])

        # Act
        value = dist_x_max(variables)

        # Assert: raw, not normalized
        assert value == pytest.approx(3.0)

    def test_should_return_the_hand_computed_raw_maximum_pairwise_distance_2d(self):
        """Given three 2-D points, returns their raw maximum pairwise distance."""
        # Arrange: pairwise distances 5, 10, 5 -> max 10
        variables = np.array([[0.0, 0.0], [3.0, 4.0], [6.0, 8.0]])

        # Act
        value = dist_x_max(variables)

        # Assert: raw, not normalized
        assert value == pytest.approx(10.0)


class TestDistFMax:
    """Unit tests for dist_f_max."""

    def test_should_return_the_hand_computed_raw_maximum_pairwise_distance_1d(self):
        """Given three single-objective vectors, returns their raw maximum pairwise distance."""
        # Arrange: objectives 2, 5, 9 -> pairwise distances 3, 7, 4 -> max 7
        objectives = np.array([[2.0], [5.0], [9.0]])

        # Act
        value = dist_f_max(objectives)

        # Assert: raw, not normalized
        assert value == pytest.approx(7.0)

    def test_should_return_the_hand_computed_raw_maximum_pairwise_distance_2d(self):
        """Given three bi-objective vectors, returns their raw maximum pairwise distance."""
        # Arrange: pairwise distances 5, 4, 3 -> max 5
        objectives = np.array([[1.0, 1.0], [4.0, 5.0], [1.0, 5.0]])

        # Act
        value = dist_f_max(objectives)

        # Assert: raw, not normalized
        assert value == pytest.approx(5.0)


class TestNdN:
    """Unit tests for nd_n."""

    def test_should_return_the_hand_verified_non_dominated_proportion(self):
        """Given a mix of non-dominated and dominated solutions, returns their proportion."""
        # Arrange: A(1,3), B(2,2), C(3,1) mutually incomparable -> front 0
        #          D(2,3) dominated by both A (1<2, 3<=3) and B (2<=2, 2<3) -> front 1
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0], [2.0, 3.0]])
        ranking = rank_solutions(objectives)

        # Act
        value = nd_n(ranking)

        # Assert: |front 0| / n = 3 / 4
        assert value == pytest.approx(0.75)

    def test_should_return_one_when_every_solution_is_non_dominated(self):
        """Given a mutually incomparable set, every solution is non-dominated."""
        # Arrange: A(1,3), B(2,2), C(3,1) mutually incomparable -> single front
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0]])
        ranking = rank_solutions(objectives)

        # Act
        value = nd_n(ranking)

        # Assert
        assert value == pytest.approx(1.0)


class TestRankAvg:
    """Unit tests for rank_avg."""

    def test_should_return_the_hand_verified_mean_rank(self):
        """Given a mix of non-dominated and dominated solutions, returns their mean rank."""
        # Arrange: same fixture as TestNdN -- ranks [0, 0, 0, 1]
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0], [2.0, 3.0]])
        ranking = rank_solutions(objectives)

        # Act
        value = rank_avg(ranking)

        # Assert: (0 + 0 + 0 + 1) / 4
        assert value == pytest.approx(0.25)

    def test_should_return_zero_when_every_solution_is_non_dominated(self):
        """Given a mutually incomparable set, every solution has rank 0."""
        # Arrange: A(1,3), B(2,2), C(3,1) mutually incomparable -> single front
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0]])
        ranking = rank_solutions(objectives)

        # Act
        value = rank_avg(ranking)

        # Assert
        assert value == pytest.approx(0.0)


class TestRankMax:
    """Unit tests for rank_max."""

    def test_should_return_the_hand_verified_maximum_rank(self):
        """Given a mix of non-dominated and dominated solutions, returns the largest rank."""
        # Arrange: same fixture as TestNdN -- ranks [0, 0, 0, 1]
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0], [2.0, 3.0]])
        ranking = rank_solutions(objectives)

        # Act
        value = rank_max(ranking)

        # Assert
        assert value == pytest.approx(1.0)

    def test_should_return_zero_when_every_solution_is_non_dominated(self):
        """Given a mutually incomparable set, every solution has rank 0."""
        # Arrange: A(1,3), B(2,2), C(3,1) mutually incomparable -> single front
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0]])
        ranking = rank_solutions(objectives)

        # Act
        value = rank_max(ranking)

        # Assert
        assert value == pytest.approx(0.0)


class TestRankEnt:
    """Unit tests for rank_ent."""

    def test_should_return_zero_when_every_solution_falls_in_a_single_front(self):
        """Given a mutually incomparable set, the front-size distribution has zero entropy."""
        # Arrange: A(1,3), B(2,2), C(3,1) mutually incomparable -> single front of size 3
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0]])
        ranking = rank_solutions(objectives)

        # Act
        value = rank_ent(ranking)

        # Assert: a single outcome with probability 1 has zero entropy
        assert value == pytest.approx(0.0)

    def test_should_return_one_bit_for_two_equally_sized_fronts(self):
        """Given two equally-sized fronts, the front-size distribution has maximum entropy."""
        # Arrange: A(1,4), B(4,1) mutually incomparable -> front 0 (size 2)
        #          C(2,4) dominated only by A, D(4,2) dominated only by B,
        #          C and D mutually incomparable -> front 1 (size 2)
        objectives = np.array([[1.0, 4.0], [4.0, 1.0], [2.0, 4.0], [4.0, 2.0]])
        ranking = rank_solutions(objectives)

        # Act
        value = rank_ent(ranking)

        # Assert: -0.5*log2(0.5) - 0.5*log2(0.5) = 1 bit, the maximum for 2 equally-likely outcomes
        assert value == pytest.approx(1.0)


class TestFCor:
    """Unit tests for f_cor."""

    def test_should_return_the_spearman_correlation_for_two_objectives(self):
        """Given M=2 perfectly rank-correlated objectives, returns their Spearman correlation."""
        # Arrange: f2 is a monotonic (rank-identical) function of f1
        objectives = np.array([[1.0, 10.0], [2.0, 20.0], [3.0, 30.0]])

        # Act
        value = f_cor(objectives)

        # Assert
        assert value == pytest.approx(1.0)

    def test_should_return_the_mean_pairwise_correlation_for_more_than_two_objectives(self):
        """Given M=3, returns the mean of the three pairwise Spearman correlations."""
        # Arrange: f1, f2 rank-identical (corr 1); f3 exactly reverse-ranked vs. both (corr -1)
        objectives = np.array(
            [
                [1.0, 10.0, 40.0],
                [2.0, 20.0, 30.0],
                [3.0, 30.0, 20.0],
                [4.0, 40.0, 10.0],
            ]
        )

        # Act
        value = f_cor(objectives)

        # Assert: (1 + (-1) + (-1)) / 3 = -1/3
        assert value == pytest.approx(-1.0 / 3.0)


class TestDistXNdMax:
    """Unit tests for dist_x_nd_max."""

    def test_should_return_the_hand_computed_maximum_excluding_the_dominated_solution(self):
        """Given a dominated solution with an extreme variable value, excludes it from the max."""
        # Arrange: same objectives as TestNdN -- front 0 = {A, B, C}, D is dominated.
        # D's variable (100) is deliberately extreme: including it (MOORPHOLOGY's pair-filter
        # bug) would give a very different, wrong maximum.
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0], [2.0, 3.0]])
        variables = np.array([[0.0], [5.0], [2.0], [100.0]])
        ranking = rank_solutions(objectives)

        # Act
        value = dist_x_nd_max(variables, ranking)

        # Assert: max pairwise distance among {0, 5, 2} only -> 5
        assert value == pytest.approx(5.0)

    def test_should_return_nan_when_fewer_than_two_solutions_are_non_dominated(self):
        """Given only one non-dominated solution, there is no pair to measure a distance over."""
        # Arrange: A(1,1) dominates B(5,5) -> front 0 = {A} only
        objectives = np.array([[1.0, 1.0], [5.0, 5.0]])
        variables = np.array([[0.0], [1.0]])
        ranking = rank_solutions(objectives)

        # Act
        value = dist_x_nd_max(variables, ranking)

        # Assert
        assert math.isnan(value)


class TestDistFAvg:
    """Unit tests for dist_f_avg."""

    def test_should_normalize_against_the_objective_space_range(self):
        """Given three bi-objective vectors, normalizes their mean pairwise distance."""
        # Arrange: same objectives as TestDistFMax's 2-D case -- distances 5, 4, 3 -> mean 4.0
        objectives = np.array([[1.0, 1.0], [4.0, 5.0], [1.0, 5.0]])
        normalizer = Normalizer(minimum=3.0, maximum=5.0)

        # Act
        value = dist_f_avg(objectives, normalizer)

        # Assert: (4.0 - 3) / (5 - 3) = 0.5
        assert value == pytest.approx(0.5)


class TestDistXNdAvg:
    """Unit tests for dist_x_nd_avg."""

    def test_should_normalize_the_mean_distance_excluding_the_dominated_solution(self):
        """Given a dominated solution with an extreme variable value, excludes it from the mean."""
        # Arrange: same objectives as TestNdN -- front 0 = {A, B, C}, D is dominated.
        # D's variable (100) is deliberately extreme: including it (MOORPHOLOGY's pair-filter
        # and wrong-divisor bugs) would give a very different, wrong mean.
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0], [2.0, 3.0]])
        variables = np.array([[0.0], [6.0], [3.0], [100.0]])
        ranking = rank_solutions(objectives)
        normalizer = Normalizer(minimum=1.0, maximum=9.0)

        # Act
        value = dist_x_nd_avg(variables, ranking, normalizer)

        # Assert: mean pairwise distance among {0, 6, 3} is 4.0; (4 - 1) / (9 - 1) = 0.375
        assert value == pytest.approx(0.375)

    def test_should_return_nan_when_fewer_than_two_solutions_are_non_dominated(self):
        """Given only one non-dominated solution, there is no pair to measure a distance over."""
        # Arrange: A(1,1) dominates B(5,5) -> front 0 = {A} only
        objectives = np.array([[1.0, 1.0], [5.0, 5.0]])
        variables = np.array([[0.0], [1.0]])
        ranking = rank_solutions(objectives)

        # Act
        value = dist_x_nd_avg(variables, ranking, Normalizer(minimum=0.0, maximum=1.0))

        # Assert
        assert math.isnan(value)


class TestFdc:
    """Unit tests for fdc."""

    def test_should_return_the_hand_verified_correlation_among_non_dominated_solutions(self):
        """Given a non-dominated front with proportional X/F distances, returns correlation 1."""
        # Arrange: four mutually incomparable objectives on a line, variables increasing in step
        # -- pairwise F-distance is exactly sqrt(2) times pairwise X-distance for every pair
        variables = np.array([[0.0], [1.0], [2.0], [3.0]])
        objectives = np.array([[1.0, 4.0], [2.0, 3.0], [3.0, 2.0], [4.0, 1.0]])
        ranking = rank_solutions(objectives)

        # Act
        value = fdc(variables, objectives, ranking)

        # Assert
        assert value == pytest.approx(1.0)

    def test_should_return_nan_when_fewer_than_two_solutions_are_non_dominated(self):
        """Given only one non-dominated solution, there is no pair to correlate."""
        # Arrange: A(1,1) dominates B(5,5) -> front 0 = {A} only
        variables = np.array([[0.0], [1.0]])
        objectives = np.array([[1.0, 1.0], [5.0, 5.0]])
        ranking = rank_solutions(objectives)

        # Act
        value = fdc(variables, objectives, ranking)

        # Assert
        assert math.isnan(value)
