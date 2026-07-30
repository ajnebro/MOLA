"""Unit tests for module mola.hull."""

import numpy as np

from mola.hull import supported_mask


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
        """Given a degenerate (collinear) set, falls back to the documented all-supported case."""
        # Arrange: A(1,3), B(2,2), C(3,1) are exactly collinear -> ConvexHull raises QhullError
        objectives = np.array([[1.0, 3.0], [2.0, 2.0], [3.0, 1.0]])

        # Act
        mask = supported_mask(objectives)

        # Assert: documented approximation, not exact
        np.testing.assert_array_equal(mask, [True, True, True])

    def test_should_return_all_true_when_at_most_m_points_are_given(self):
        """Given |points| <= M, every point is supported by construction."""
        # Arrange: two points, M = 2 -> ConvexHull is skipped entirely
        objectives = np.array([[1.0, 2.0], [2.0, 1.0]])

        # Act
        mask = supported_mask(objectives)

        # Assert
        np.testing.assert_array_equal(mask, [True, True])
