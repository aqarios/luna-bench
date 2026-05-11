"""Tests for the Runtime metric."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.components.metrics.runtime import Runtime, RuntimeResult

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from tests.unit.fixtures.mock_feature_results import SolutionFactory


def _create_empty_feature_results() -> FeatureResults:
    """Create empty FeatureResults (Runtime doesn't need features)."""
    return FeatureResults(data={})


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

    def test_captures_runtime(self, create_solution: SolutionFactory) -> None:
        """Test that the metric captures a solution runtime."""
        expected_runtime = 0.1
        solution = create_solution(obj_values=[1.0], feasible=[True], runtime_seconds=expected_runtime)
        feature_results = _create_empty_feature_results()

        metric = Runtime()
        result = metric.run(solution, feature_results)

        assert isinstance(result, RuntimeResult)
        # Allow some tolerance for timing variations
        assert result.runtime_seconds == pytest.approx(expected_runtime, abs=0.05)

    def test_different_runtimes(self, create_solution: SolutionFactory) -> None:
        """Test that different solution runtimes are captured correctly."""
        solution_fast = create_solution(obj_values=[1.0], feasible=[True], runtime_seconds=0.05)
        solution_slow = create_solution(obj_values=[1.0], feasible=[True], runtime_seconds=0.15)
        feature_results = _create_empty_feature_results()

        metric = Runtime()
        result_fast = metric.run(solution_fast, feature_results)
        result_slow = metric.run(solution_slow, feature_results)

        assert isinstance(result_fast, RuntimeResult)
        assert isinstance(result_slow, RuntimeResult)
        assert result_fast.runtime_seconds < result_slow.runtime_seconds

    def test_none_runtime_returns_infinity(
        self, mock_solution_config: MagicMock, mock_feature_results: MagicMock
    ) -> None:
        """Test that a solution with runtime=None returns inf."""
        mock_solution_config.runtime = None

        result = Runtime().run(mock_solution_config, mock_feature_results)

        assert isinstance(result, RuntimeResult)
        assert result.runtime_seconds == float("inf")
