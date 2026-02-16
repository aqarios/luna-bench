"""Tests for QuboMatrixFeature."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from numpy.typing import NDArray

from luna_bench.components.features.qubo.matrix_features import (
    QuboMatrixFeature,
    QuboMatrixFeatureResult,
)
from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper


class TestQuboMatrixFeature:
    """Tests for the QuboMatrixFeature extractor."""

    @staticmethod
    def _run_with_matrix(matrix: NDArray[np.float64]) -> QuboMatrixFeatureResult:
        mock_model = MagicMock()
        with patch(
            "luna_bench.components.features.qubo.matrix_features.get_qubo",
            return_value=matrix,
        ):
            return QuboMatrixFeature().run(mock_model)

    def test_returns_correct_result_type(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(sample_qubo_matrix)
        assert isinstance(result, QuboMatrixFeatureResult)

    def test_mean_computed_correctly(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(sample_qubo_matrix)
        assert result.mean == pytest.approx(NumpyStatsHelper.mean(sample_qubo_matrix))

    def test_median_computed_correctly(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(sample_qubo_matrix)
        assert result.median == pytest.approx(NumpyStatsHelper.median(sample_qubo_matrix))

    def test_variance_computed_correctly(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(sample_qubo_matrix)
        assert result.variance == pytest.approx(NumpyStatsHelper.var(sample_qubo_matrix))

    def test_std_computed_correctly(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(sample_qubo_matrix)
        assert result.std == pytest.approx(NumpyStatsHelper.std(sample_qubo_matrix))

    def test_minimum_computed_correctly(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(sample_qubo_matrix)
        assert result.minium == pytest.approx(np.min(sample_qubo_matrix))

    def test_maximum_computed_correctly(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(sample_qubo_matrix)
        assert result.maximum == pytest.approx(np.max(sample_qubo_matrix))

    def test_skewness_computed_correctly(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(sample_qubo_matrix)
        assert result.skewness == pytest.approx(NumpyStatsHelper.skew(sample_qubo_matrix.flatten()))

    def test_kurtosis_computed_correctly(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(sample_qubo_matrix)
        assert result.kurtosis == pytest.approx(NumpyStatsHelper.kurtosis(sample_qubo_matrix.flatten()))

    def test_quantiles_computed_correctly(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(sample_qubo_matrix)
        assert result.q10 == pytest.approx(NumpyStatsHelper.q10(sample_qubo_matrix))
        assert result.q90 == pytest.approx(NumpyStatsHelper.q90(sample_qubo_matrix))

    def test_vc_computed_correctly(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(sample_qubo_matrix)
        assert result.vc == pytest.approx(NumpyStatsHelper.vc(sample_qubo_matrix))

    def test_identity_matrix(self) -> None:
        identity = np.eye(3)
        result = self._run_with_matrix(identity)

        assert result.mean == pytest.approx(np.mean(identity))
        assert result.std == pytest.approx(np.std(identity))

    def test_q10_less_than_or_equal_q90(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(sample_qubo_matrix)
        assert result.q10 <= result.q90

    def test_deterministic_results(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result1 = self._run_with_matrix(sample_qubo_matrix)
        result2 = self._run_with_matrix(sample_qubo_matrix)

        assert result1.mean == result2.mean
        assert result1.variance == result2.variance
        assert result1.std == result2.std
