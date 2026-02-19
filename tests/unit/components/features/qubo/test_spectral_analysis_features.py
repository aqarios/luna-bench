"""Tests for QuboSpectralAnalysisFeature."""

import numpy as np
import pytest
from numpy.typing import NDArray

from luna_bench.components.features.qubo.spectral_analysis_features import (
    QuboSpectralAnalysisFeature,
)

from .run_with_matrix import run_with_matrix


class TestQuboSpectralAnalysisFeature:
    """Tests for the QuboSpectralAnalysisFeature extractor."""

    feature = QuboSpectralAnalysisFeature()

    def test_eigenvalue_stats(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = run_with_matrix(sample_qubo_matrix, feature=self.feature)

        assert result.mean_eigenvalue == pytest.approx(2.6666666667, rel=1e-6)
        assert result.median_eigenvalue == pytest.approx(3.3027756377, rel=1e-6)
        assert result.std_eigenvalue == pytest.approx(2.2110831936, rel=1e-6)
        assert result.q10_eigenvalue == pytest.approx(0.4183346174, rel=1e-6)
        assert result.q90_eigenvalue == pytest.approx(4.6605551275, rel=1e-6)
        assert result.minimum_eigenvalue == pytest.approx(-0.3027756377, rel=1e-6)
        assert result.maximum_eigenvalue == pytest.approx(5.0)
        assert result.dominant_eigenvalue == pytest.approx(5.0)
        assert result.dominant_eigenvector == pytest.approx(0.8312507835, rel=1e-6)
        assert result.condition_number == pytest.approx(16.5138781887, rel=1e-6)
        assert result.vc_eigenvalue == pytest.approx(0.8291561976, rel=1e-6)

    def test_eigenvector_stats(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = run_with_matrix(sample_qubo_matrix, feature=self.feature)

        assert result.mean_eigenvector == pytest.approx(0.2066506777, rel=1e-6)
        assert result.median_eigenvector == pytest.approx(0.3333333333, rel=1e-6)
        assert result.std_eigenvector == pytest.approx(0.5391000192, rel=1e-6)
        assert result.minimum_eigenvector == pytest.approx(-0.5414666348, rel=1e-6)
        assert result.maximum_eigenvector == pytest.approx(0.8312507835, rel=1e-6)

    def test_identity_matrix_eigenvalues(self) -> None:
        identity = np.eye(3)
        result = run_with_matrix(identity, feature=self.feature)

        assert result.mean_eigenvalue == pytest.approx(1.0)
        assert result.minimum_eigenvalue == pytest.approx(1.0)
        assert result.maximum_eigenvalue == pytest.approx(1.0)
        assert result.dominant_eigenvalue == pytest.approx(1.0)
        assert result.std_eigenvalue == pytest.approx(0.0)
        assert result.condition_number == pytest.approx(1.0)

    def test_deterministic_results(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result1 = run_with_matrix(sample_qubo_matrix, feature=self.feature)
        result2 = run_with_matrix(sample_qubo_matrix, feature=self.feature)
        assert result1 == result2
