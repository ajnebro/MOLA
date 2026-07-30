"""Unit tests for module mola.features.multimodality."""

import math

import numpy as np
import pytest

from mola.distance import Neighbourhood
from mola.dominance import neighbourhood_dominance
from mola.features import nd_per_plo, plo_dist_avg, plo_dist_max, plo_n
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
