"""Tests for QuboSparsityDensityFeature."""

import numpy as np
import pytest
from numpy.typing import NDArray

from luna_bench.components.features.qubo.sparsity_density_features import (
    QuboSparsityDensityFeature,
    QuboSparsityDensityFeatureResult,
)

from .run_with_matrix import run_with_matrix


class TestQuboSparsityDensityFeature:
    """Tests for the QuboSparsityDensityFeature extractor."""

    feature = QuboSparsityDensityFeature()

    def test_returns_correct_result_type(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = run_with_matrix(sample_qubo_matrix, feature=self.feature)
        assert isinstance(result, QuboSparsityDensityFeatureResult)

    def test_computes_correct_values_for_sparse_matrix(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = run_with_matrix(sample_qubo_matrix, feature=self.feature)

        # 3x3 matrix: [[1,2,0],[2,3,1],[0,1,4]] → 7 non-zero, 2 zero, 9 total
        assert result.num_variables == 3
        assert result.num_non_zero == 7
        assert result.num_zero == 2
        assert result.density == pytest.approx(7 / 9)
        assert result.sparsity == pytest.approx(2 / 9)

    def test_sparsity_plus_density_equals_one(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = run_with_matrix(sample_qubo_matrix, feature=self.feature)
        assert result.sparsity + result.density == pytest.approx(1.0)

    def test_fully_dense_matrix(self, fully_connected_qubo_matrix: NDArray[np.float64]) -> None:
        result = run_with_matrix(fully_connected_qubo_matrix, feature=self.feature)

        assert result.num_zero == 0
        assert result.num_non_zero == 9
        assert result.sparsity == pytest.approx(0.0)
        assert result.density == pytest.approx(1.0)

    def test_diagonal_matrix(self, diagonal_qubo_matrix: NDArray[np.float64]) -> None:
        result = run_with_matrix(diagonal_qubo_matrix, feature=self.feature)

        # 3x3 diagonal: 3 non-zero (diagonal), 6 zero (off-diagonal)
        assert result.num_variables == 3
        assert result.num_non_zero == 3
        assert result.num_zero == 6
        assert result.sparsity == pytest.approx(6 / 9)
        assert result.density == pytest.approx(3 / 9)

    def test_all_zeros_matrix(self) -> None:
        matrix = np.zeros((3, 3))
        result = run_with_matrix(matrix, feature=self.feature)

        assert result.num_non_zero == 0
        assert result.num_zero == 9
        assert result.num_variables == 3
        assert result.sparsity == pytest.approx(1.0)
        assert result.density == pytest.approx(0.0)
