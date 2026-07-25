"""Unit tests for module mola.normalization."""

import numpy as np
import pytest

from mola.normalization import Normalizer, build_normalizers


class TestNormalizer:
    """Unit tests for Normalizer.normalize."""

    def test_should_map_minimum_to_zero_and_maximum_to_one(self):
        """Given a non-degenerate range, normalizes linearly onto [0, 1]."""
        # Arrange
        normalizer = Normalizer(minimum=1.0, maximum=3.0)

        # Act & Assert
        assert normalizer.normalize(1.0) == pytest.approx(0.0)
        assert normalizer.normalize(3.0) == pytest.approx(1.0)
        assert normalizer.normalize(2.0) == pytest.approx(0.5)

    def test_should_return_zero_when_range_is_degenerate(self):
        """Given minimum == maximum, returns 0.0 instead of dividing by zero."""
        # Arrange: every pairwise distance in the sample was identical.
        normalizer = Normalizer(minimum=5.0, maximum=5.0)

        # Act & Assert
        assert normalizer.normalize(5.0) == pytest.approx(0.0)


class TestBuildNormalizers:
    """Unit tests for build_normalizers."""

    def test_should_build_independent_normalizers_per_space(self):
        """Given known variable- and objective-space points, builds two independent normalizers."""
        # Arrange: variable-space pairwise distances are 1, 3, 2 (min=1, max=3);
        # objective-space pairwise distances are 5, 10, 5 (min=5, max=10).
        variables = np.array([[0.0], [1.0], [3.0]])
        objectives = np.array([[0.0, 0.0], [3.0, 4.0], [6.0, 8.0]])

        # Act
        normalizers = build_normalizers(variables, objectives)

        # Assert
        assert normalizers.variable_space.minimum == pytest.approx(1.0)
        assert normalizers.variable_space.maximum == pytest.approx(3.0)
        assert normalizers.objective_space.minimum == pytest.approx(5.0)
        assert normalizers.objective_space.maximum == pytest.approx(10.0)
