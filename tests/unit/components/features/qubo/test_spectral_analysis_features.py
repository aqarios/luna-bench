"""Tests for QuboSpectralAnalysisFeature."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from numpy.typing import NDArray

from luna_bench.components.features.qubo.spectral_analysis_features import (
    QuboSpectralAnalysisFeature,
    QuboSpectralAnalysisFeatureResult,
)
from luna_bench.components.helper.numpy_stats_helper import NumpyStatsHelper


class TestQuboSpectralAnalysisFeature:
    """Tests for the QuboSpectralAnalysisFeature extractor."""

    @staticmethod
    def _run_with_matrix(matrix: NDArray[np.float64]) -> QuboSpectralAnalysisFeatureResult:
        mock_model = MagicMock()
        with patch(
            "luna_bench.components.features.qubo.spectral_analysis_features.get_qubo",
            return_value=matrix,
        ):
            return QuboSpectralAnalysisFeature().run(mock_model)

    def test_returns_correct_result_type(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(sample_qubo_matrix)
        assert isinstance(result, QuboSpectralAnalysisFeatureResult)

    def test_eigenvalue_stats_match_manual_computation(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        eigenvalues, _ = np.linalg.eigh(sample_qubo_matrix)
        result = self._run_with_matrix(sample_qubo_matrix)

        assert result.mean_eigenvalue == pytest.approx(NumpyStatsHelper.mean(eigenvalues))
        assert result.median_eigenvalue == pytest.approx(NumpyStatsHelper.median(eigenvalues))
        assert result.std_eigenvalue == pytest.approx(NumpyStatsHelper.std(eigenvalues))
        assert result.q10_eigenvalue == pytest.approx(NumpyStatsHelper.q10(eigenvalues))
        assert result.q90_eigenvalue == pytest.approx(NumpyStatsHelper.q90(eigenvalues))
        assert result.minimum_eigenvalue == pytest.approx(NumpyStatsHelper.min(eigenvalues))
        assert result.maximum_eigenvalue == pytest.approx(NumpyStatsHelper.max(eigenvalues))

    def test_eigenvector_stats_match_manual_computation(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        _, eigenvectors = np.linalg.eigh(sample_qubo_matrix)
        result = self._run_with_matrix(sample_qubo_matrix)

        assert result.mean_eigenvector == pytest.approx(NumpyStatsHelper.mean(eigenvectors))
        assert result.median_eigenvector == pytest.approx(NumpyStatsHelper.median(eigenvectors))
        assert result.std_eigenvector == pytest.approx(NumpyStatsHelper.std(eigenvectors))
        assert result.minimum_eigenvector == pytest.approx(NumpyStatsHelper.min(eigenvectors))
        assert result.maximum_eigenvector == pytest.approx(NumpyStatsHelper.max(eigenvectors))

    def test_dominant_eigenvalue_is_max_absolute(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        eigenvalues, _ = np.linalg.eigh(sample_qubo_matrix)
        result = self._run_with_matrix(sample_qubo_matrix)

        expected_dominant = np.max(np.abs(eigenvalues))
        assert result.dominant_eigenvalue == pytest.approx(expected_dominant)

    def test_dominant_eigenvector_is_max_absolute(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        _, eigenvectors = np.linalg.eigh(sample_qubo_matrix)
        result = self._run_with_matrix(sample_qubo_matrix)

        expected_dominant = np.max(np.abs(eigenvectors))
        assert result.dominant_eigenvector == pytest.approx(expected_dominant)

    def test_condition_number(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = self._run_with_matrix(sample_qubo_matrix)

        expected_cond = np.linalg.cond(sample_qubo_matrix)
        assert result.condition_number == pytest.approx(expected_cond)

    def test_identity_matrix_eigenvalues(self) -> None:
        identity = np.eye(3)
        result = self._run_with_matrix(identity)

        # All eigenvalues of identity matrix are 1
        assert result.mean_eigenvalue == pytest.approx(1.0)
        assert result.minimum_eigenvalue == pytest.approx(1.0)
        assert result.maximum_eigenvalue == pytest.approx(1.0)
        assert result.dominant_eigenvalue == pytest.approx(1.0)
        assert result.std_eigenvalue == pytest.approx(0.0)
        assert result.condition_number == pytest.approx(1.0)

    def test_vc_eigenvalue(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        eigenvalues, _ = np.linalg.eigh(sample_qubo_matrix)
        result = self._run_with_matrix(sample_qubo_matrix)

        assert result.vc_eigenvalue == pytest.approx(NumpyStatsHelper.vc(eigenvalues))

    def test_deterministic_results(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result1 = self._run_with_matrix(sample_qubo_matrix)
        result2 = self._run_with_matrix(sample_qubo_matrix)

        assert result1.mean_eigenvalue == result2.mean_eigenvalue
        assert result1.condition_number == result2.condition_number
        assert result1.dominant_eigenvalue == result2.dominant_eigenvalue
