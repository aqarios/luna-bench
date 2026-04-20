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

    # --- min ---

    def test_min_returns_minimum_value(self) -> None:
        data = np.array([3.0, 1.0, 4.0, 1.5, 9.0])
        assert NumpyStatsHelper.min(data) == pytest.approx(1.0)

    def test_min_with_negative_values(self) -> None:
        data = np.array([2.0, -5.0, 3.0])
        assert NumpyStatsHelper.min(data) == pytest.approx(-5.0)

    def test_min_single_element(self) -> None:
        data = np.array([7.0])
        assert NumpyStatsHelper.min(data) == pytest.approx(7.0)

    def test_min_2d_array(self) -> None:
        data = np.array([[3.0, 1.0], [4.0, 0.5]])
        assert NumpyStatsHelper.min(data) == pytest.approx(0.5)

    # --- max ---

    def test_max_returns_maximum_value(self) -> None:
        data = np.array([3.0, 1.0, 4.0, 1.5, 9.0])
        assert NumpyStatsHelper.max(data) == pytest.approx(9.0)

    def test_max_with_negative_values(self) -> None:
        data = np.array([-2.0, -5.0, -3.0])
        assert NumpyStatsHelper.max(data) == pytest.approx(-2.0)

    def test_max_single_element(self) -> None:
        data = np.array([7.0])
        assert NumpyStatsHelper.max(data) == pytest.approx(7.0)

    def test_max_2d_array(self) -> None:
        data = np.array([[3.0, 1.0], [4.0, 0.5]])
        assert NumpyStatsHelper.max(data) == pytest.approx(4.0)

    def test_min_less_than_or_equal_max(self) -> None:
        data = np.array([5.0, 2.0, 8.0, 1.0])
        assert NumpyStatsHelper.min(data) <= NumpyStatsHelper.max(data)

    # --- skew ---

    def test_skew_symmetric_distribution(self) -> None:
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        assert NumpyStatsHelper.skew(data) == pytest.approx(0.0)

    def test_skew_right_skewed(self) -> None:
        data = np.array([1.0, 1.0, 1.0, 1.0, 10.0])
        assert NumpyStatsHelper.skew(data) > 0

    def test_skew_left_skewed(self) -> None:
        data = np.array([10.0, 10.0, 10.0, 10.0, 1.0])
        assert NumpyStatsHelper.skew(data) < 0

    def test_skew_empty_returns_zero(self) -> None:
        data = np.array([])
        assert NumpyStatsHelper.skew(data) == 0.0

    def test_skew_matches_scipy(self) -> None:
        from scipy.stats import skew as scipy_skew

        data = np.array([2.0, 3.0, 5.0, 7.0, 11.0, 13.0])
        assert NumpyStatsHelper.skew(data) == pytest.approx(float(scipy_skew(data)))

    # --- kurtosis ---

    def test_kurtosis_normal_like_distribution(self) -> None:
        rng = np.random.default_rng(42)
        data = rng.normal(0, 1, 10000)
        assert NumpyStatsHelper.kurtosis(data) == pytest.approx(0.0, abs=0.1)

    def test_kurtosis_uniform_is_negative(self) -> None:
        data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        assert NumpyStatsHelper.kurtosis(data) < 0

    def test_kurtosis_heavy_tails_is_positive(self) -> None:
        data = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 100.0])
        assert NumpyStatsHelper.kurtosis(data) > 0

    def test_kurtosis_empty_returns_zero(self) -> None:
        data = np.array([])
        assert NumpyStatsHelper.kurtosis(data) == 0.0

    def test_kurtosis_matches_scipy(self) -> None:
        from scipy.stats import kurtosis as scipy_kurtosis

        data = np.array([2.0, 3.0, 5.0, 7.0, 11.0, 13.0])
        assert NumpyStatsHelper.kurtosis(data) == pytest.approx(float(scipy_kurtosis(data)))
