"""Unit tests for module mola.geometry."""

import numpy as np
import pytest

from mola.geometry import (
    DEFAULT_GEOMETRY,
    DEFAULT_OBJECTIVE_SCALING,
    Geometry,
    ObjectiveScaling,
    decision_space,
    objective_space,
)
from mola.sample import Sample


def _make_sample(lower_bounds: np.ndarray, upper_bounds: np.ndarray) -> Sample:
    return Sample(
        problem="P",
        variables=np.array([[0.0, 5.0, 2.0], [10.0, 7.5, 2.0], [5.0, 10.0, 2.0]]),
        objectives=np.zeros((3, 2)),
        lower_bounds=lower_bounds,
        upper_bounds=upper_bounds,
        sampler="lhs",
    )


class TestDecisionSpace:
    """Unit tests for decision_space."""

    def test_should_default_to_the_bound_geometry(self):
        """The default geometry is bound (research/decisions/decisions.md, D1)."""
        # Assert
        assert DEFAULT_GEOMETRY is Geometry.BOUND

    def test_should_return_the_variables_unchanged_under_raw(self):
        """Given the raw geometry, returns the sample's own decision vectors."""
        # Arrange
        sample = _make_sample(np.array([0.0, 5.0, 2.0]), np.array([10.0, 10.0, 2.0]))

        # Act
        variables = decision_space(sample, Geometry.RAW)

        # Assert
        np.testing.assert_array_equal(variables, sample.variables)

    def test_should_map_each_variable_to_the_unit_interval_under_bound(self):
        """Given the bound geometry, maps each variable through its own bounds."""
        # Arrange: x1 in [0, 10], x2 in [5, 10]
        sample = _make_sample(np.array([0.0, 5.0, 0.0]), np.array([10.0, 10.0, 4.0]))

        # Act
        variables = decision_space(sample, Geometry.BOUND)

        # Assert
        np.testing.assert_allclose(variables, [[0.0, 0.0, 0.5], [1.0, 0.5, 0.5], [0.5, 1.0, 0.5]])

    def test_should_map_a_fixed_variable_to_zero_under_bound(self):
        """Given a variable whose bounds are equal, maps it to 0 for every solution."""
        # Arrange: x3 is fixed at 2
        sample = _make_sample(np.array([0.0, 5.0, 2.0]), np.array([10.0, 10.0, 2.0]))

        # Act
        variables = decision_space(sample, Geometry.BOUND)

        # Assert
        np.testing.assert_array_equal(variables[:, 2], [0.0, 0.0, 0.0])

    def test_should_raise_error_for_infinite_bounds_under_bound(self):
        """Given an unbounded variable, the bound geometry raises ValueError naming it."""
        # Arrange
        sample = _make_sample(np.array([0.0, -np.inf, 2.0]), np.array([10.0, 10.0, 2.0]))

        # Act & Assert
        with pytest.raises(ValueError, match=r"variable\(s\) \[2\]"):
            decision_space(sample, Geometry.BOUND)

    def test_should_accept_the_geometry_name_as_a_string(self):
        """Given "raw" as a plain string, behaves as Geometry.RAW."""
        # Arrange
        sample = _make_sample(np.array([0.0, 5.0, 2.0]), np.array([10.0, 10.0, 2.0]))

        # Act
        variables = decision_space(sample, "raw")

        # Assert
        np.testing.assert_array_equal(variables, sample.variables)

    def test_should_raise_error_for_an_unknown_geometry(self):
        """Given an unknown geometry name, raises ValueError."""
        # Arrange
        sample = _make_sample(np.array([0.0, 5.0, 2.0]), np.array([10.0, 10.0, 2.0]))

        # Act & Assert
        with pytest.raises(ValueError, match="sample-range"):
            decision_space(sample, "sample-range")


def _make_objective_sample(objectives: np.ndarray) -> Sample:
    return Sample(
        problem="P",
        variables=np.zeros((objectives.shape[0], 1)),
        objectives=objectives,
        lower_bounds=np.zeros(1),
        upper_bounds=np.ones(1),
        sampler="lhs",
    )


class TestObjectiveSpace:
    """Unit tests for objective_space."""

    def test_should_default_to_raw_objectives(self):
        """The default objective scaling keeps the paper's raw objective values."""
        # Assert
        assert DEFAULT_OBJECTIVE_SCALING is ObjectiveScaling.RAW

    def test_should_return_the_objectives_unchanged_under_raw(self):
        """Given the raw profile, returns the sample's own objective vectors."""
        # Arrange
        sample = _make_objective_sample(np.array([[1.0, 300.0], [3.0, 100.0], [2.0, 200.0]]))

        # Act
        objectives = objective_space(sample, ObjectiveScaling.RAW)

        # Assert
        np.testing.assert_array_equal(objectives, sample.objectives)

    def test_should_map_each_objective_to_the_unit_interval_under_sample(self):
        """Given the sample profile, min-max scales each objective over the sample."""
        # Arrange
        sample = _make_objective_sample(np.array([[1.0, 300.0], [3.0, 100.0], [2.0, 200.0]]))

        # Act
        objectives = objective_space(sample, "sample")

        # Assert
        np.testing.assert_allclose(objectives, [[0.0, 1.0], [1.0, 0.0], [0.5, 0.5]])

    def test_should_map_a_constant_objective_to_zero_under_sample(self):
        """Given an objective with the same value everywhere, maps it to 0."""
        # Arrange
        sample = _make_objective_sample(np.array([[1.0, 7.0], [3.0, 7.0]]))

        # Act
        objectives = objective_space(sample, ObjectiveScaling.SAMPLE)

        # Assert
        np.testing.assert_array_equal(objectives[:, 1], [0.0, 0.0])
