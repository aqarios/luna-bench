"""Tests for the BestSolutionFound metric."""

from __future__ import annotations

import time
from collections.abc import Mapping

import pytest
from luna_quantum import Sense, Solution, Timer, Vtype

from luna_bench.base_components import BaseFeature
from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.components.features.optsol_feature import OptSolFeature, OptSolFeatureResult
from luna_bench.components.metrics.best_solution_found import (
    BestSolutionFound,
    BestSolutionFoundError,
    BestSolutionFoundResult,
)
from luna_bench.types import FeatureName, FeatureResult


def _create_solution(
    obj_values: list[float],
    sense: Sense = Sense.Min,
    runtime_seconds: float = 0.1,
) -> Solution:
    """Helper to create a Solution with specific objective values."""
    timer = Timer.start()
    time.sleep(runtime_seconds)
    timing = timer.stop()

    num_samples = len(obj_values)
    return Solution._build(  # type: ignore[attr-defined,no-any-return]
        component_types=[Vtype.Binary],
        binary_cols=[[0] * num_samples],
        raw_energies=obj_values,
        timing=timing,
        counts=[1] * num_samples,
        sense=sense,
        obj_values=obj_values,
        feasible=[True] * num_samples,
    )


def _create_feature_results(optimal_value: float) -> FeatureResults:
    """Helper to create FeatureResults with OptSolFeature result."""
    opt_feature = OptSolFeature()
    opt_result = OptSolFeatureResult(best_sol=optimal_value, pre_terminated=False)
    data: Mapping[type[BaseFeature], Mapping[FeatureName, tuple[FeatureResult, BaseFeature]]] = {
        OptSolFeature: {"optsol": (opt_result, opt_feature)}  # type: ignore[dict-item]
    }
    return FeatureResults(allowed=[OptSolFeature], data=data)


class TestBestSolutionFoundResult:
    """Tests for BestSolutionFoundResult validation."""

    def test_valid_result_optimal(self) -> None:
        """Test that a BSF of 1.0 (optimal) is valid."""
        result = BestSolutionFoundResult(best_solution_found=1.0)
        assert result.best_solution_found == 1.0

    def test_valid_result_suboptimal(self) -> None:
        """Test that a BSF > 1.0 (suboptimal) is valid."""
        result = BestSolutionFoundResult(best_solution_found=1.5)
        assert result.best_solution_found == 1.5

    def test_valid_result_infinity(self) -> None:
        """Test that infinity is valid (no solution found)."""
        result = BestSolutionFoundResult(best_solution_found=float("inf"))
        assert result.best_solution_found == float("inf")

    def test_invalid_result_less_than_one(self) -> None:
        """Test that BSF < 1.0 raises an error."""
        with pytest.raises(BestSolutionFoundError):
            BestSolutionFoundResult(best_solution_found=0.9)


class TestBestSolutionFound:
    """Tests for the BestSolutionFound metric."""

    def test_optimal_solution_minimization(self) -> None:
        """Test BSF = 1.0 when best found equals optimal (minimization)."""
        solution = _create_solution(obj_values=[10.0, 5.0, 15.0], sense=Sense.Min)
        feature_results = _create_feature_results(optimal_value=5.0)

        metric = BestSolutionFound()
        result = metric.run(solution, feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == 1.0

    def test_suboptimal_solution_minimization(self) -> None:
        """Test BSF > 1.0 when best found is worse than optimal (minimization)."""
        solution = _create_solution(obj_values=[10.0, 8.0, 15.0], sense=Sense.Min)
        feature_results = _create_feature_results(optimal_value=4.0)

        metric = BestSolutionFound()
        result = metric.run(solution, feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == 2.0  # 8.0 / 4.0

    def test_optimal_solution_maximization(self) -> None:
        """Test BSF = 1.0 when best found equals optimal (maximization)."""
        solution = _create_solution(obj_values=[10.0, 20.0, 15.0], sense=Sense.Max)
        feature_results = _create_feature_results(optimal_value=20.0)

        metric = BestSolutionFound()
        result = metric.run(solution, feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == 1.0

    def test_suboptimal_solution_maximization(self) -> None:
        """Test BSF > 1.0 when best found is worse than optimal (maximization)."""
        solution = _create_solution(obj_values=[10.0, 15.0, 12.0], sense=Sense.Max)
        feature_results = _create_feature_results(optimal_value=30.0)

        metric = BestSolutionFound()
        result = metric.run(solution, feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == 2.0  # 30.0 / 15.0

    def test_empty_solution(self) -> None:
        """Test that empty solution returns infinity."""
        timer = Timer.start()
        time.sleep(0.01)
        timing = timer.stop()

        solution = Solution._build(  # type: ignore[attr-defined]
            component_types=[Vtype.Binary],
            binary_cols=[[]],
            timing=timing,
            sense=Sense.Min,
        )
        feature_results = _create_feature_results(optimal_value=5.0)

        metric = BestSolutionFound()
        result = metric.run(solution, feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == float("inf")

    def test_division_by_zero_raises_error(self) -> None:
        """Test that division by zero (optimal = 0) raises NotImplementedError."""
        solution = _create_solution(obj_values=[10.0, 5.0], sense=Sense.Min)
        feature_results = _create_feature_results(optimal_value=0.0)

        metric = BestSolutionFound()

        with pytest.raises(NotImplementedError, match="dividing by 0"):
            metric.run(solution, feature_results)

    def test_custom_tolerance(self) -> None:
        """Test that custom absolute tolerance is respected."""
        solution = _create_solution(obj_values=[10.0, 5.0], sense=Sense.Min)
        feature_results = _create_feature_results(optimal_value=0.0001)

        # With default tolerance (1e-3), this should raise
        metric_default = BestSolutionFound()
        with pytest.raises(NotImplementedError):
            metric_default.run(solution, feature_results)

        # With smaller tolerance, it should work
        metric_small_tol = BestSolutionFound(abs_tol=1e-6)
        result = metric_small_tol.run(solution, feature_results)
        assert result.best_solution_found == 5.0 / 0.0001
