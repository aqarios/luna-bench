"""Tests for the ApproximationRatio metric."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from luna_model import Sense
from pydantic import ValidationError

from luna_bench.metrics.approximation_ratio import (
    ApproximationRatio,
    ApproximationRatioResult,
)

if TYPE_CHECKING:
    from unittest.mock import MagicMock


class TestApproximationRatio:
    """Tests for the ApproximationRatio metric class."""

    @pytest.mark.parametrize("mock_feature_results", [10.0], indirect=True)
    def test_no_solution_returns_negative_infinity(
        self, mock_solution_config: MagicMock, mock_feature_results: MagicMock
    ) -> None:
        """Test that when no solution is found, the approximation ratio is negative infinity."""
        result = ApproximationRatio().run(mock_solution_config, mock_feature_results)

        assert isinstance(result, ApproximationRatioResult)
        assert result.approximation_ratio == float("-inf")

    @pytest.mark.parametrize("mock_solution_config", [(Sense.MIN, 5.0)], indirect=True)
    def test_optimal_solution_zero_raises_error(
        self, mock_solution_config: MagicMock, mock_feature_results: MagicMock
    ) -> None:
        """Test that ZeroDivisionError is raised when the optimal solution is zero.

        This is a special edge case, which we currently do not support.
        """
        metric = ApproximationRatio()
        with pytest.raises(ZeroDivisionError) as exc_info:
            metric.run(mock_solution_config, mock_feature_results)

        assert "Approximation Ratio is not implemented for cases dividing by 0!" in str(exc_info.value)

    @pytest.mark.parametrize(
        ("mock_solution_config", "mock_feature_results"),
        [((Sense.MIN, 5.0), 1e-4)],
        indirect=True,
    )
    def test_optimal_solution_near_zero_raises_error(
        self, mock_solution_config: MagicMock, mock_feature_results: MagicMock
    ) -> None:
        """Test that ZeroDivisionError is raised when the optimal solution is near zero.

        The default absolute tolerance in ApproximationRatio is 1e-3, so 1e-4 should raise.
        """
        metric = ApproximationRatio()

        with pytest.raises(ZeroDivisionError):
            metric.run(mock_solution_config, mock_feature_results)

    @pytest.mark.parametrize(
        ("mock_solution_config", "mock_feature_results"),
        [((Sense.MIN, 1e-2), 1e-2)],
        indirect=True,
    )
    def test_optimal_solution_above_tolerance(
        self, mock_solution_config: MagicMock, mock_feature_results: MagicMock
    ) -> None:
        """Test that calculation proceeds when optimal is just above the tolerance threshold."""
        metric = ApproximationRatio(abt_diff=1e-3)
        result = metric.run(mock_solution_config, mock_feature_results)

        assert isinstance(result, ApproximationRatioResult)
        assert result.approximation_ratio == pytest.approx(1.0)

    @pytest.mark.parametrize(
        ("mock_solution_config", "mock_feature_results", "expected_ratio"),
        [
            # AR = 1 - abs(expectation_value - optimal) / abs(optimal), sense-agnostic.
            # Minimization
            ((Sense.MIN, 10.0), 10.0, 1.0),  # Perfect: 1 - |10-10|/10 = 1.0
            ((Sense.MIN, 20.0), 10.0, 0.0),  # Worse: 1 - |20-10|/10 = 0.0
            ((Sense.MIN, 15.0), 10.0, 0.5),  # Worse: 1 - |15-10|/10 = 0.5
            # Maximization
            ((Sense.MAX, 100.0), 100.0, 1.0),  # Perfect: 1 - |100-100|/100 = 1.0
            ((Sense.MAX, 50.0), 100.0, 0.5),  # Worse: 1 - |50-100|/100 = 0.5
            ((Sense.MAX, 20.0), 100.0, 0.2),  # Worse: 1 - |20-100|/100 = 0.2
            # Negative / mixed-sign optimal: abs keeps the metric monotonic
            ((Sense.MIN, 0.0), -5.0, 0.0),  # opt=-5, exp=0:  1 - |0-(-5)|/5 = 0.0
            ((Sense.MIN, -2.5), -5.0, 0.5),  # opt=-5, exp=-2.5: 1 - |-2.5+5|/5 = 0.5
            ((Sense.MAX, -50.0), 100.0, -0.5),  # opt=100, exp=-50: 1 - |-50-100|/100 = -0.5
        ],
        indirect=["mock_solution_config", "mock_feature_results"],
    )
    def test_parametrized_approximation_ratios(
        self,
        mock_solution_config: MagicMock,
        mock_feature_results: MagicMock,
        expected_ratio: float,
    ) -> None:
        """Parametrized test for various approximation ratio scenarios."""
        result = ApproximationRatio().run(mock_solution_config, mock_feature_results)

        assert isinstance(result, ApproximationRatioResult)
        assert result.approximation_ratio == pytest.approx(expected_ratio)


class TestApproximationRatioResult:
    """Tests for the ApproximationRatioResult class."""

    def test_raise_error_invalid_approximation_ratio(self) -> None:
        """Test that an invalid approximation ratio raises an error."""
        with pytest.raises(ValidationError, match=r"Input should be less than or equal to 1"):
            ApproximationRatioResult(approximation_ratio=1.5)

    def test_result_serialization(self) -> None:
        """Test that the result can be serialized to dict."""
        result = ApproximationRatioResult(approximation_ratio=-0.5)
        result_dict = result.model_dump()

        assert "approximation_ratio" in result_dict
        assert result_dict["approximation_ratio"] == -0.5
