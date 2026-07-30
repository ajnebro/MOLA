"""Unit tests for module mola.hypervolume."""

import numpy as np
import pytest

from mola.hypervolume import reference_point, singleton_hypervolume


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
