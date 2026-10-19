"""Unit tests for module mola.hull."""

import numpy as np
import pytest

from mola.hull import (
    _min_max_scale,
    _supported_by_linear_programs,
    _supported_on_chain,
    _supported_on_dominated_hull,
    supported_mask,
)
from mola.ranking import rank_solutions


def _random_nondominated_set(
    rng: np.random.Generator, count: int, number_of_objectives: int, variant: int
) -> np.ndarray:
    """A random mutually non-dominated set, with ties, plateaus or duplicates by `variant`."""
    points = rng.random((count, number_of_objectives))
    if variant == 1:
        points = np.round(points, 1)  # many ties on single objectives
    elif variant == 2:
        points[:, 0] = 0.0  # a plateau: one objective constant over the set
    points = points[rank_solutions(points).rank == 0]
    if variant == 3:
        points = np.vstack([points, points[:1]])  # an exact duplicate
    return points


class TestSupportedMask:
    """Unit tests for supported_mask."""

    def test_should_exclude_a_notch_point_from_the_convex_hull(self):
        """Given a point not reachable by any linear scalarization, excludes it from the mask."""
        # Arrange: A(1,5), B(2,2), D(5,1) form the convex hull's minimizing facets; C(3,1.8)
        # sits in the "notch" between B and D, off the hull entirely
        objectives = np.array([[1.0, 5.0], [2.0, 2.0], [3.0, 1.8], [5.0, 1.0]])

        # Act
        mask = supported_mask(objectives)

        # Assert
        np.testing.assert_array_equal(mask, [True, True, False, True])

    def test_should_return_all_true_for_a_proper_convex_front(self):
        """Given a non-degenerate convex front, every point is supported."""
        # Arrange: A(1,4), B(2,2), C(4,1), a proper (non-collinear) triangle
        objectives = np.array([[1.0, 4.0], [2.0, 2.0], [4.0, 1.0]])

        # Act
        mask = supported_mask(objectives)

        # Assert
        np.testing.assert_array_equal(mask, [True, True, True])

    def test_should_return_all_true_when_the_set_is_collinear(self):
        """Given collinear points on a minimizing edge, every point is supported."""
        # Arrange: A(1,3), B(2,2), C(3,1) all minimize f1 + f2 (weights (1/2, 1/2))
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0]])

        # Act
        mask = supported_mask(objectives)

        # Assert
        np.testing.assert_array_equal(mask, [True, True, True])

    def test_should_return_all_true_for_two_bi_objective_points(self):
        """Given two mutually non-dominated bi-objective points, both are supported."""
        # Arrange
        objectives = np.array([[1.0, 2.0], [2.0, 1.0]])

        # Act
        mask = supported_mask(objectives)

        # Assert
        np.testing.assert_array_equal(mask, [True, True])

    def test_should_exclude_a_point_dominated_by_a_segment_even_with_at_most_m_points(self):
        """Given three tri-objective points (|set| = M), still excludes the unsupported one."""
        # Arrange (phase 0, case A): C(0.6,0.6,0.6) is dominated by 0.5*A + 0.5*B =
        # (0.5,0.5,0.5), so no weighting makes it a minimizer. The 0.2.0 shortcut
        # "|set| <= M -> all supported" marked it supported.
        objectives = np.array([[0.0, 1.0, 1.0], [1.0, 0.0, 0.0], [0.6, 0.6, 0.6]])

        # Act
        mask = supported_mask(objectives)

        # Assert
        np.testing.assert_array_equal(mask, [True, True, False])

    def test_should_include_a_point_inside_a_minimizing_facet(self):
        """Given a point strictly inside a minimizing edge, it is supported but not extreme."""
        # Arrange (phase 0, case B): B(0.5,1.5) lies on the edge from A(0,2) to C(2,0), tying
        # with both under weights (1/2, 1/2); D(1.5,1) lies above that edge
        objectives = np.array([[0.0, 2.0], [0.5, 1.5], [2.0, 0.0], [1.5, 1.0]])

        # Act
        mask = supported_mask(objectives)

        # Assert
        np.testing.assert_array_equal(mask, [True, True, True, False])

    def test_should_include_a_vertex_whose_incident_facets_all_face_away(self):
        """Given a supported vertex none of whose hull facets has an all-negative normal."""
        # Arrange (phase 0, case C): D(0.8,0.9,0.1) is the unique minimizer of f3, hence of
        # weights close to (0,0,1), but every facet of the plain convex hull through D has a
        # positive normal component. The 0.2.0 facet test missed it.
        objectives = np.array([[0.4, 0.5, 0.3], [0.9, 0.2, 0.8], [0.5, 0.3, 0.7], [0.8, 0.9, 0.1]])

        # Act
        mask = supported_mask(objectives)

        # Assert
        np.testing.assert_array_equal(mask, [True, True, True, True])

    def test_should_not_let_a_plateau_objective_make_every_tied_point_supported(self):
        """Given a constant objective, only a zero weight would make the middle point optimal."""
        # Arrange: f1 is 0 everywhere, so weights (1,0,0) tie all three points; with strictly
        # positive weights, A(0,6,6) is dominated by 0.5*B + 0.5*C = (0,5,5)
        objectives = np.array([[0.0, 6.0, 6.0], [0.0, 0.0, 10.0], [0.0, 10.0, 0.0]])

        # Act
        mask = supported_mask(objectives)

        # Assert
        np.testing.assert_array_equal(mask, [False, True, True])

    def test_should_give_duplicated_points_the_same_verdict(self):
        """Given an exact duplicate of a supported point, both copies are supported."""
        # Arrange
        objectives = np.array([[1.0, 4.0], [2.0, 2.0], [2.0, 2.0], [4.0, 1.0]])

        # Act
        mask = supported_mask(objectives)

        # Assert
        np.testing.assert_array_equal(mask, [True, True, True, True])

    def test_should_return_all_true_for_a_single_objective(self):
        """Given M = 1, every (necessarily tied) non-dominated point is supported."""
        # Arrange
        objectives = np.array([[3.0], [3.0]])

        # Act
        mask = supported_mask(objectives)

        # Assert
        np.testing.assert_array_equal(mask, [True, True])

    def test_should_return_an_empty_mask_for_an_empty_set(self):
        """Given no points, returns an empty mask."""
        # Arrange
        objectives = np.zeros((0, 3))

        # Act
        mask = supported_mask(objectives)

        # Assert
        assert mask.shape == (0,)

    def test_should_be_invariant_to_positive_per_objective_affine_maps(self):
        """Given the same set in other units, returns the same mask."""
        # Arrange
        objectives = np.array(
            [[0.4, 0.5, 0.3], [0.9, 0.2, 0.8], [0.5, 0.3, 0.7], [0.8, 0.9, 0.1], [0.7, 0.7, 0.7]]
        )
        rescaled = objectives * np.array([1e-3, 1.0, 1e4]) + np.array([5.0, -2.0, 100.0])

        # Act
        mask = supported_mask(objectives)
        rescaled_mask = supported_mask(rescaled)

        # Assert
        np.testing.assert_array_equal(mask, rescaled_mask)


class TestExactMethodsAgree:
    """The three exact methods behind supported_mask must agree on every input."""

    @pytest.mark.parametrize("variant", [0, 1, 2, 3])
    def test_should_agree_between_chain_and_linear_programs_for_two_objectives(self, variant):
        """Given random bi-objective sets, the convex chain matches the LP verdicts."""
        # Arrange
        rng = np.random.default_rng(100 + variant)
        sets = [
            _random_nondominated_set(rng, int(rng.integers(1, 30)), 2, variant) for _ in range(40)
        ]

        for points in sets:
            scaled = _min_max_scale(points)

            # Act
            chain = _supported_on_chain(scaled)
            linear_programs = _supported_by_linear_programs(scaled)

            # Assert
            np.testing.assert_array_equal(chain, linear_programs)

    @pytest.mark.parametrize("number_of_objectives", [3, 4])
    @pytest.mark.parametrize("variant", [0, 1, 2, 3])
    def test_should_agree_between_dominated_hull_and_linear_programs(
        self, number_of_objectives, variant
    ):
        """Given random sets with ties, plateaus or duplicates, the hull matches the LPs."""
        # Arrange
        rng = np.random.default_rng(10 * number_of_objectives + variant)
        sets = [
            _random_nondominated_set(rng, int(rng.integers(1, 20)), number_of_objectives, variant)
            for _ in range(15)
        ]

        for points in sets:
            scaled = _min_max_scale(points)

            # Act
            hull = _supported_on_dominated_hull(scaled)
            linear_programs = _supported_by_linear_programs(scaled)

            # Assert
            np.testing.assert_array_equal(hull, linear_programs)
