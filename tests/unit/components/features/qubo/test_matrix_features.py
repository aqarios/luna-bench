"""Tests for QuboMatrixFeature."""

import numpy as np
import pytest
from numpy.typing import NDArray

from luna_bench.components.features.qubo.matrix_features import (
    QuboMatrixFeature,
)

from .run_with_matrix import run_with_matrix


class TestQuboMatrixFeature:
    """Tests for the QuboMatrixFeature extractor."""

    features = QuboMatrixFeature()

    def test_identity_matrix(self) -> None:
        identity = np.eye(3)
        result = run_with_matrix(identity, feature=self.features)

        assert result.mean == pytest.approx(1 / 3)
        assert result.std == pytest.approx(np.sqrt((3 * (1 - 1 / 3) ** 2 + 6 * (0 - 1 / 3) ** 2) / 9))

    def test_q10_less_than_or_equal_q90(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result = run_with_matrix(sample_qubo_matrix, feature=self.features)
        assert result.q10 <= result.q90

    def test_deterministic_results(self, sample_qubo_matrix: NDArray[np.float64]) -> None:
        result1 = run_with_matrix(sample_qubo_matrix, feature=self.features)
        result2 = run_with_matrix(sample_qubo_matrix, feature=self.features)
        assert result1 == result2
