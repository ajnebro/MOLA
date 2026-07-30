"""Unit tests for module mola.features.multimodality."""

import math

import numpy as np
import pytest

from mola.distance import Neighbourhood
from mola.dominance import neighbourhood_dominance
from mola.features import (
    eval_aws,
    length_aws,
    nd_per_plo,
    plo_dist_avg,
    plo_dist_max,
    plo_n,
    slo_dist_avg,
    slo_dist_max,
    slo_n,
)
from mola.multimodality import AdaptiveWalks
from mola.normalization import Normalizer
from mola.ranking import rank_solutions


class TestPloN:
    """Unit tests for plo_n."""

    def test_should_include_a_globally_dominated_solution_whose_neighbour_does_not_dominate_it(
        self,
    ):
        """A solution can be a Pareto local optimum while globally dominated, and vice versa."""
        # Arrange: A(1,5), B(5,1) mutually incomparable; E(2,6) is dominated globally by A, but
        # E's only neighbour is B (not A), and B doesn't dominate E -> E is still a PLO.
        # G(6,6) is dominated by both A and B; G's only neighbour is E, which dominates G
        # (2<=6, 6<=6) -> G is not a PLO. Hand-picked neighbourhoods (k=1), not spatial.
        objectives = np.array([[1.0, 5.0], [5.0, 1.0], [2.0, 6.0], [6.0, 6.0]])
        indices = np.array([[1], [0], [1], [2]])  # A->B, B->A, E->B, G->E
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)

        # Act
        value = plo_n(dominance)

        # Assert: PLO = {A, B, E}, G is the only non-PLO solution -> 3 / 4
        assert value == pytest.approx(0.75)

    def test_should_return_one_for_a_mutual_anti_chain(self):
        """Given a mutually incomparable set, every solution is trivially a Pareto local optimum."""
        # Arrange: A(1,3), B(2,2), C(3,1) mutually incomparable, k=2
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)

        # Act
        value = plo_n(dominance)

        # Assert
        assert value == pytest.approx(1.0)


class TestPloDistAvg:
    """Unit tests for plo_dist_avg."""

    def test_should_normalize_the_hand_computed_mean_distance_among_plo_solutions(self):
        """Given the plo_n fixture above, normalizes the mean pairwise distance among PLO only."""
        # Arrange: same objectives/neighbourhoods as TestPloN's first case -- PLO = {A, B, E},
        # with 1-D variables 0, 8, 2, 4 (A, B, E, G). Whole-sample pairwise distances range
        # [2, 8]; among PLO {0, 8, 2}: distances 8, 2, 6 -> mean 16/3.
        objectives = np.array([[1.0, 5.0], [5.0, 1.0], [2.0, 6.0], [6.0, 6.0]])
        variables = np.array([[0.0], [8.0], [2.0], [4.0]])
        indices = np.array([[1], [0], [1], [2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)
        normalizer = Normalizer(minimum=2.0, maximum=8.0)

        # Act
        value = plo_dist_avg(variables, dominance, normalizer)

        # Assert: (16/3 - 2) / (8 - 2) = 5/9
        assert value == pytest.approx(5.0 / 9.0)

    def test_should_return_nan_when_fewer_than_two_solutions_are_plo(self):
        """Given only one Pareto local optimum, there is no pair to measure a distance over."""
        # Arrange: A(5,5) is dominated by its only neighbour B(1,1) -> not PLO.
        #          B(1,1) is not dominated by its only neighbour A(5,5) -> the sole PLO.
        objectives = np.array([[5.0, 5.0], [1.0, 1.0]])
        variables = np.array([[0.0], [1.0]])
        indices = np.array([[1], [0]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)

        # Act
        value = plo_dist_avg(variables, dominance, Normalizer(minimum=0.0, maximum=1.0))

        # Assert
        assert math.isnan(value)


class TestPloDistMax:
    """Unit tests for plo_dist_max."""

    def test_should_return_the_hand_computed_raw_maximum_distance_among_plo_solutions(self):
        """Given the plo_n fixture above, returns the raw maximum distance among PLO only."""
        # Arrange: same fixture as TestPloDistAvg -- PLO variables {0, 8, 2}, max distance 8
        objectives = np.array([[1.0, 5.0], [5.0, 1.0], [2.0, 6.0], [6.0, 6.0]])
        variables = np.array([[0.0], [8.0], [2.0], [4.0]])
        indices = np.array([[1], [0], [1], [2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)

        # Act
        value = plo_dist_max(variables, dominance)

        # Assert: raw, not normalized
        assert value == pytest.approx(8.0)

    def test_should_return_nan_when_fewer_than_two_solutions_are_plo(self):
        """Given only one Pareto local optimum, there is no pair to measure a distance over."""
        # Arrange: same fixture as TestPloDistAvg's NaN case
        objectives = np.array([[5.0, 5.0], [1.0, 1.0]])
        variables = np.array([[0.0], [1.0]])
        indices = np.array([[1], [0]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)

        # Act
        value = plo_dist_max(variables, dominance)

        # Assert
        assert math.isnan(value)


class TestNdPerPlo:
    """Unit tests for nd_per_plo."""

    def test_should_return_the_hand_verified_ratio_when_nd_n_and_plo_n_differ(self):
        """Given the plo_n fixture above, returns nd_n / plo_n -- not the other way around."""
        # Arrange: same objectives as TestPloN's first case.
        # Global ranking: front 0 = {A, B} (nd_n = 2/4 = 0.5); PLO = {A, B, E} (plo_n = 3/4 = 0.75).
        objectives = np.array([[1.0, 5.0], [5.0, 1.0], [2.0, 6.0], [6.0, 6.0]])
        indices = np.array([[1], [0], [1], [2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)
        ranking = rank_solutions(objectives)

        # Act
        value = nd_per_plo(ranking, dominance)

        # Assert: 0.5 / 0.75 = 2/3 (not 0.75 / 0.5 = 1.5 -- catches a flipped division)
        assert value == pytest.approx(2.0 / 3.0)

    def test_should_return_one_for_a_mutual_anti_chain(self):
        """Given a mutually incomparable set, both nd_n and plo_n are 1."""
        # Arrange: A(1,3), B(2,2), C(3,1) mutually incomparable, k=2
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        dominance = neighbourhood_dominance(objectives, neighbourhood)
        ranking = rank_solutions(objectives)

        # Act
        value = nd_per_plo(ranking, dominance)

        # Assert
        assert value == pytest.approx(1.0)


class TestSloN:
    """Unit tests for slo_n."""

    def test_should_return_the_hand_verified_mean_proportion(self):
        """Given a complete neighbourhood, returns the mean per-objective local-optimum share."""
        # Arrange: A(1,5), B(3,2), C(2,4), D(5,1), everyone else is a neighbour (k=3).
        # A is the sole f_1 local optimum, D the sole f_2 local optimum -> mean(1/4, 1/4) = 0.25
        objectives = np.array([[1.0, 5.0], [3.0, 2.0], [2.0, 4.0], [5.0, 1.0]])
        indices = np.array([[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        value = slo_n(objectives, neighbourhood)

        # Assert
        assert value == pytest.approx(0.25)

    def test_should_allow_more_than_one_local_optimum_per_objective(self):
        """Given two disconnected neighbour pairs, each can independently be a local optimum."""
        # Arrange: A(1,9)-B(5,9) and C(2,9)-D(8,9) are disconnected mutual-neighbour pairs.
        # A and C are both f_1 local optima; f_2 is constant, so everyone is an f_2 local optimum
        # -> mean(2/4, 4/4) = 0.75
        objectives = np.array([[1.0, 9.0], [5.0, 9.0], [2.0, 9.0], [8.0, 9.0]])
        indices = np.array([[1], [0], [3], [2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        value = slo_n(objectives, neighbourhood)

        # Assert
        assert value == pytest.approx(0.75)


class TestSloDistAvg:
    """Unit tests for slo_dist_avg."""

    def test_should_return_the_hand_computed_mean_across_objectives(self):
        """Given the disconnected-pairs fixture, averages normalized distance across objectives."""
        # Arrange: same objectives as TestSloN's second case. Variables 0, 1, 10, 11 (A, B, C, D).
        # f_1 local optima {A, C} = {0, 10} -> mean pairwise distance 10.
        # f_2 local optima {A, B, C, D} = {0, 1, 10, 11} -> mean pairwise distance 7.0.
        # Whole-sample range [1, 11]: normalize(10) = 0.9, normalize(7.0) = 0.6 -> mean 0.75
        objectives = np.array([[1.0, 9.0], [5.0, 9.0], [2.0, 9.0], [8.0, 9.0]])
        variables = np.array([[0.0], [1.0], [10.0], [11.0]])
        indices = np.array([[1], [0], [3], [2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        normalizer = Normalizer(minimum=1.0, maximum=11.0)

        # Act
        value = slo_dist_avg(variables, objectives, neighbourhood, normalizer)

        # Assert
        assert value == pytest.approx(0.75)

    def test_should_return_nan_when_every_objective_has_fewer_than_two_local_optima(self):
        """Given the fully-connected fixture, each objective has exactly one local optimum."""
        # Arrange: same objectives as TestSloN's first case -- both S_1 and S_2 have size 1
        objectives = np.array([[1.0, 5.0], [3.0, 2.0], [2.0, 4.0], [5.0, 1.0]])
        variables = np.array([[0.0], [1.0], [2.0], [3.0]])
        indices = np.array([[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        normalizer = Normalizer(minimum=1.0, maximum=3.0)

        # Act
        value = slo_dist_avg(variables, objectives, neighbourhood, normalizer)

        # Assert
        assert math.isnan(value)


class TestSloDistMax:
    """Unit tests for slo_dist_max."""

    def test_should_return_the_hand_computed_mean_across_objectives(self):
        """Given the disconnected-pairs fixture, averages the raw maximum across objectives."""
        # Arrange: same fixture as TestSloDistAvg -- f_1 local optima {0, 10} (max 10),
        # f_2 local optima {0, 1, 10, 11} (max 11) -> mean(10, 11) = 10.5
        objectives = np.array([[1.0, 9.0], [5.0, 9.0], [2.0, 9.0], [8.0, 9.0]])
        variables = np.array([[0.0], [1.0], [10.0], [11.0]])
        indices = np.array([[1], [0], [3], [2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        value = slo_dist_max(variables, objectives, neighbourhood)

        # Assert
        assert value == pytest.approx(10.5)

    def test_should_return_nan_when_every_objective_has_fewer_than_two_local_optima(self):
        """Given the fully-connected fixture, each objective has exactly one local optimum."""
        # Arrange: same objectives as TestSloN's first case -- both S_1 and S_2 have size 1
        objectives = np.array([[1.0, 5.0], [3.0, 2.0], [2.0, 4.0], [5.0, 1.0]])
        variables = np.array([[0.0], [1.0], [2.0], [3.0]])
        indices = np.array([[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )

        # Act
        value = slo_dist_max(variables, objectives, neighbourhood)

        # Assert
        assert math.isnan(value)


class TestLengthAws:
    """Unit tests for length_aws."""

    def test_should_return_the_mean_walk_length(self):
        """Given the five hand-traced walks, returns their mean length."""
        # Arrange: lengths from the chain fixture in test_multimodality.py: 0, 1, 2, 3, 4
        walks = AdaptiveWalks(
            lengths=np.array([0, 1, 2, 3, 4]), evaluations=np.array([2, 3, 4, 6, 7])
        )

        # Act
        value = length_aws(walks)

        # Assert: (0 + 1 + 2 + 3 + 4) / 5 = 2.0
        assert value == pytest.approx(2.0)


class TestEvalAws:
    """Unit tests for eval_aws."""

    def test_should_return_the_mean_evaluation_count(self):
        """Given the five hand-traced walks, returns their mean evaluation count."""
        # Arrange: same walks as TestLengthAws
        walks = AdaptiveWalks(
            lengths=np.array([0, 1, 2, 3, 4]), evaluations=np.array([2, 3, 4, 6, 7])
        )

        # Act
        value = eval_aws(walks)

        # Assert: (2 + 3 + 4 + 6 + 7) / 5 = 22 / 5 = 4.4
        assert value == pytest.approx(4.4)
