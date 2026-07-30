"""Unit tests for module mola.hypervolume."""

import numpy as np
import pytest

from mola.distance import Neighbourhood
from mola.hypervolume import (
    neighbour_hypervolume_difference,
    neighbourhood_hypervolume,
    reference_point,
    singleton_hypervolume,
)


class TestReferencePoint:
    """Unit tests for reference_point."""

    def test_should_return_the_hand_computed_per_objective_maximum(self):
        """Given three bi-objective vectors, returns the per-objective maximum."""
        # Arrange
        objectives = np.array([[1.0, 5.0], [3.0, 2.0], [4.0, 4.0]])

        # Act
        ref = reference_point(objectives)

        # Assert: max(1, 3, 4) = 4; max(5, 2, 4) = 5
        np.testing.assert_allclose(ref, [4.0, 5.0])


class TestSingletonHypervolume:
    """Unit tests for singleton_hypervolume."""

    def test_should_return_the_hand_computed_per_solution_box_volume(self):
        """Given a fixed reference point, returns each solution's box-hypervolume against it."""
        # Arrange
        objectives = np.array([[2.0, 3.0], [10.0, 10.0], [5.0, 8.0]])
        ref = np.array([10.0, 10.0])

        # Act
        result = singleton_hypervolume(objectives, ref)

        # Assert: (10-2)*(10-3)=56; a solution AT the reference has zero volume; (10-5)*(10-8)=10
        np.testing.assert_allclose(result, [56.0, 0.0, 10.0])

    def test_should_return_zero_for_a_solution_worse_than_the_reference_in_any_objective(self):
        """Given a solution outside the reference box, its box-volume is clamped to zero."""
        # Arrange: worse than ref in the second objective (12 > 10)
        objectives = np.array([[2.0, 12.0]])
        ref = np.array([10.0, 10.0])

        # Act
        result = singleton_hypervolume(objectives, ref)

        # Assert
        assert result[0] == pytest.approx(0.0)


class TestNeighbourHypervolumeDifference:
    """Unit tests for neighbour_hypervolume_difference."""

    def test_should_return_the_hand_computed_per_neighbour_hypervolume_difference(self):
        """Given three objective vectors, returns |hv(i) - hv(j)| for each neighbour pair."""
        # Arrange: objectives (0,0), (3,4), (0,8) -> ref=(3,8) -> hv = [24, 0, 0]
        # everyone else is a neighbour (k=2)
        objectives = np.array([[0.0, 0.0], [3.0, 4.0], [0.0, 8.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        ref = reference_point(objectives)

        # Act
        result = neighbour_hypervolume_difference(objectives, neighbourhood, ref)

        # Assert: solution 0 (hv=24) vs 1 (hv=0) and 2 (hv=0): |24-0|=24 both
        np.testing.assert_allclose(result[0], [24.0, 24.0])
        # solution 1 (hv=0) vs 0 (hv=24) and 2 (hv=0): 24, 0
        np.testing.assert_allclose(result[1], [24.0, 0.0])
        # solution 2 (hv=0) vs 0 (hv=24) and 1 (hv=0): 24, 0
        np.testing.assert_allclose(result[2], [24.0, 0.0])


class TestNeighbourhoodHypervolume:
    """Unit tests for neighbourhood_hypervolume."""

    def test_should_return_the_moocore_verified_per_neighbourhood_hypervolume(self):
        """Given four objective vectors, returns the joint hypervolume of each one's neighbours."""
        # Arrange: A(1,4), B(2,2), C(4,1), D(6,6) -> ref=(6,6). Neighbourhoods hand-picked
        # (not spatial): A->{B,C}, B->{A,C}, C->{A,B}, D->{A,B}. Expected values cross-checked
        # against moocore.hypervolume directly on each 2-point subset: [18, 16, 18, 18]
        objectives = np.array([[1.0, 4.0], [2.0, 2.0], [4.0, 1.0], [6.0, 6.0]])
        indices = np.array([[1, 2], [0, 2], [0, 1], [0, 1]])
        neighbourhood = Neighbourhood(
            indices=indices, distances=np.zeros_like(indices, dtype=float)
        )
        ref = reference_point(objectives)

        # Act
        result = neighbourhood_hypervolume(objectives, neighbourhood, ref)

        # Assert
        np.testing.assert_allclose(result, [18.0, 16.0, 18.0, 18.0])
