"""Tests for the ApproximationRatio metric."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from luna_quantum import Sense
from pydantic import ValidationError

from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.components.features.optsol_feature import OptSolFeature, OptSolFeatureResult
from luna_bench.components.metrics.approximation_ratio import (
    ApproximationRatio,
    ApproximationRatioResult,
)


def _create_mock_solution(
    sense: Sense,
    expectation_value: float | None,
) -> MagicMock:
    """Create a mock Solution object with configurable objective value, sense, and expectation value.

    Args:
        obj_value: The best solution's objective value (None if no solution found)
        sense: Optimization sense (Min or Max)
        expectation_value: The average/expectation value of all solutions.
                          If None, defaults to obj_value for convenience.
    """
    solution = MagicMock(spec=["best", "sense", "expectation_value", "samples"])
    solution.sense = sense

    if expectation_value is None:  # empty solution
        solution.best.return_value = None
        solution.expectation_value.return_value = None
        solution.samples = []
    else:
        best_sample = MagicMock()
        solution.best.return_value = best_sample
        solution.expectation_value.return_value = expectation_value
        solution.samples = [best_sample]

    return solution


def _create_mock_feature_results(optimal_value: float) -> MagicMock:
    """Create a mock FeatureResults object with a given optimal solution value."""
    opt_sol_result = OptSolFeatureResult(best_sol=optimal_value, runtime=1.0, pre_terminated=False)
    opt_sol_feature = OptSolFeature()

    feature_results = MagicMock(spec=FeatureResults)
    feature_results.first.return_value = (opt_sol_result, opt_sol_feature)

    return feature_results


class TestApproximationRatio:
    """Tests for the ApproximationRatio metric class."""

    def test_no_solution_returns_infinity(self) -> None:
        """Test that when no solution is found, the approximation ratio is infinity."""
        solution = _create_mock_solution(expectation_value=None, sense=Sense.Min)
        feature_results = _create_mock_feature_results(optimal_value=10.0)

        metric = ApproximationRatio()
        result = metric.run(solution, feature_results)

        assert isinstance(result, ApproximationRatioResult)
        assert result.approximation_ratio == float("inf")

    def test_optimal_solution_zero_raises_error(self) -> None:
        """Test that NotImplementedError is raised when optimal solution is zero."""
        solution = _create_mock_solution(expectation_value=5.0, sense=Sense.Min)
        feature_results = _create_mock_feature_results(optimal_value=0.0)

        metric = ApproximationRatio()

        with pytest.raises(NotImplementedError) as exc_info:
            metric.run(solution, feature_results)

        assert "Approximation Ratio is not implemented for cases dividing by 0!" in str(exc_info.value)

    def test_optimal_solution_near_zero_raises_error(self) -> None:
        """Test that NotImplementedError is raised when optimal solution is near zero."""
        solution = _create_mock_solution(expectation_value=5.0, sense=Sense.Min)
        feature_results = _create_mock_feature_results(optimal_value=1e-4)

        metric = ApproximationRatio()

        with pytest.raises(NotImplementedError):
            metric.run(solution, feature_results)

    def test_optimal_solution_just_above_tolerance(self) -> None:
        """Test that calculation proceeds when optimal is just above the tolerance threshold."""
        target_diff = 1e-2
        solution = _create_mock_solution(expectation_value=target_diff, sense=Sense.Min)
        feature_results = _create_mock_feature_results(optimal_value=target_diff)

        metric = ApproximationRatio(abt_diff=1e-3)
        result = metric.run(solution, feature_results)

        assert isinstance(result, ApproximationRatioResult)
        assert result.approximation_ratio == pytest.approx(1.0)

    @pytest.mark.parametrize(
        ("found_value", "optimal_value", "sense", "expected_ratio"),
        [
            # Minimization: AR = expectation_value / optimal ignore
            (10.0, 10.0, Sense.Min, 1.0),  # Perfect: 10/10 = 1.0
            (20.0, 10.0, Sense.Min, 2.0),  # Worse: 20/10 = 2.0
            (15.0, 10.0, Sense.Min, 1.5),  # Worse: 15/10 = 1.5
            # Maximization: AR = optimal / expectation_value     # noqa: ERA001
            (100.0, 100.0, Sense.Max, 1.0),  # Perfect: 100/100 = 1.0
            (50.0, 100.0, Sense.Max, 2.0),  # Worse: 100/50 = 2.0
            (20.0, 100.0, Sense.Max, 5.0),  # Worse: 100/20 = 5.0
        ],
    )
    def test_parametrized_approximation_ratios(
        self,
        found_value: float,
        optimal_value: float,
        sense: Sense,
        expected_ratio: float,
    ) -> None:
        """Parametrized test for various approximation ratio scenarios."""
        solution = _create_mock_solution(expectation_value=found_value, sense=sense)
        feature_results = _create_mock_feature_results(optimal_value=optimal_value)

        metric = ApproximationRatio()
        result = metric.run(solution, feature_results)

        assert isinstance(result, ApproximationRatioResult)
        assert result.approximation_ratio == pytest.approx(expected_ratio)


class TestApproximationRatioResult:
    """Tests for the ApproximationRatioResult class."""

    def test_raise_error_invalid_approximation_ratio(self) -> None:
        """Test that an invalid approximation ratio raises an error."""
        with pytest.raises(ValidationError, match=r"Approximation Ratio must be >= 1\.0 by definition of metric\."):
            ApproximationRatioResult(approximation_ratio=0.5)

    def test_result_model_fields(self) -> None:
        """Test that ApproximationRatioResult has the expected field."""
        result = ApproximationRatioResult(approximation_ratio=1)
        assert hasattr(result, "approximation_ratio")
        assert result.approximation_ratio == 1

    def test_result_serialization(self) -> None:
        """Test that the result can be serialized to dict."""
        result = ApproximationRatioResult(approximation_ratio=1.5)
        result_dict = result.model_dump()

        assert "approximation_ratio" in result_dict
        assert result_dict["approximation_ratio"] == 1.5
