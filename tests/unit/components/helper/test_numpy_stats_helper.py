"""Tests for NumpyStatsHelper class."""

import numpy as np
import pytest

from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper


class TestNumpyStatsHelper:
    """Test suite for NumpyStatsHelper."""

    def test_var_with_data(self) -> None:
        """Test variance calculation with non-empty data."""
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = NumpyStatsHelper.var(data)
        assert result == pytest.approx(data.var())

    def test_var_with_empty_data(self) -> None:
        """Test variance calculation returns 0 for empty array."""
        data = np.array([])
        result = NumpyStatsHelper.var(data)
        assert result == 0.0

    def test_normalized_with_data(self) -> None:
        """Test normalization with non-zero sum."""
        data = np.array([1.0, 2.0, 3.0, 4.0])
        result = NumpyStatsHelper.normalized(data)
        expected = data / np.sum(data)
        np.testing.assert_array_almost_equal(result, expected)
        assert np.sum(result) == pytest.approx(1.0)

    def test_normalized_with_zero_sum(self) -> None:
        """Test normalization returns original array when sum is zero."""
        data = np.array([0.0, 0.0, 0.0])
        result = NumpyStatsHelper.normalized(data)
        np.testing.assert_array_equal(result, data)

    def test_sqrt_normalized_with_data(self) -> None:
        """Test sqrt normalization with non-zero sum."""
        data = np.array([1.0, 2.0, 3.0, 4.0])
        result = NumpyStatsHelper.sqrt_normalized(data)
        normalized = data / np.sum(data)
        expected = np.sqrt(normalized)
        np.testing.assert_array_almost_equal(result, expected)

    def test_sqrt_normalized_with_zero_sum(self) -> None:
        """Test sqrt normalization returns sqrt of original when sum is zero."""
        data = np.array([0.0, 0.0, 0.0])
        result = NumpyStatsHelper.sqrt_normalized(data)
        expected = np.sqrt(data)
        np.testing.assert_array_equal(result, expected)
