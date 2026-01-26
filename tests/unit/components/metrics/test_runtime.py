"""Tests for the Runtime metric."""

from __future__ import annotations

import time

from luna_quantum import Sense, Solution, Timer, Vtype

from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.components.metrics.runtime import Runtime, RuntimeResult


def _create_solution(runtime_seconds: float = 0.1) -> Solution:
    """Helper to create a Solution with specific runtime."""
    timer = Timer.start()
    time.sleep(runtime_seconds)
    timing = timer.stop()

    return Solution._build(  # type: ignore[attr-defined,no-any-return]
        component_types=[Vtype.Binary],
        binary_cols=[[0]],
        raw_energies=[1.0],
        timing=timing,
        counts=[1],
        sense=Sense.Min,
        obj_values=[1.0],
        feasible=[True],
    )


def _create_empty_feature_results() -> FeatureResults:
    """Helper to create empty FeatureResults (Runtime doesn't need features)."""
    return FeatureResults(allowed=[], data={})


class TestRuntimeResult:
    """Tests for RuntimeResult."""

    def test_valid_result(self) -> None:
        """Test that RuntimeResult stores runtime correctly."""
        result = RuntimeResult(runtime_seconds=1.5)
        assert result.runtime_seconds == 1.5

    def test_zero_runtime(self) -> None:
        """Test that zero runtime is valid."""
        result = RuntimeResult(runtime_seconds=0.0)
        assert result.runtime_seconds == 0.0


class TestRuntime:
    """Tests for the Runtime metric."""

    def test_captures_runtime(self) -> None:
        """Test that the metric captures solution runtime."""
        expected_runtime = 0.1
        solution = _create_solution(runtime_seconds=expected_runtime)
        feature_results = _create_empty_feature_results()

        metric = Runtime()
        result = metric.run(solution, feature_results)

        assert isinstance(result, RuntimeResult)
        # Allow some tolerance for timing variations
        assert result.runtime_seconds >= expected_runtime
        assert result.runtime_seconds < expected_runtime + 0.05

    def test_different_runtimes(self) -> None:
        """Test that different solution runtimes are captured correctly."""
        solution_fast = _create_solution(runtime_seconds=0.05)
        solution_slow = _create_solution(runtime_seconds=0.15)
        feature_results = _create_empty_feature_results()

        metric = Runtime()
        result_fast = metric.run(solution_fast, feature_results)
        result_slow = metric.run(solution_slow, feature_results)

        assert isinstance(result_fast, RuntimeResult)
        assert isinstance(result_slow, RuntimeResult)
        assert result_fast.runtime_seconds < result_slow.runtime_seconds
