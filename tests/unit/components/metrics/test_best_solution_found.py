"""Tests for the BestSolutionFound metric."""

from __future__ import annotations

import time
from unittest.mock import MagicMock, PropertyMock

import pytest
from luna_quantum import Sense, Solution, Timer, Vtype
from pydantic import ValidationError

from luna_bench.components.metrics.best_solution_found import (
    BestSolutionFound,
    BestSolutionFoundResult,
)
from tests.unit.fixtures import create_solution


class TestBestSolutionFoundResult:
    """Tests for BestSolutionFoundResult validation."""

    def test_valid_result_infinity(self) -> None:
        """Test that infinity is valid (no solution found)."""
        result = BestSolutionFoundResult(best_solution_found=float("inf"))
        assert result.best_solution_found == float("inf")

    def test_invalid_result_less_than_one(self) -> None:
        """Test that BSF < 1.0 raises an error."""
        with pytest.raises(ValidationError):
            BestSolutionFoundResult(best_solution_found=0.9)


class TestBestSolutionFound:
    """Tests for the BestSolutionFound metric."""

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_optimal_solution_minimization(self, mock_feature_results: MagicMock) -> None:
        """Test BSF = 1.0 when best found equals optimal (minimization)."""
        solution = create_solution(obj_values=[10.0, 5.0, 15.0], sense=Sense.Min)
        result = BestSolutionFound().run(solution, mock_feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == 1.0

    @pytest.mark.parametrize("mock_feature_results", [4.0], indirect=True)
    def test_suboptimal_solution_minimization(self, mock_feature_results: MagicMock) -> None:
        """Test BSF > 1.0 when best found is worse than optimal (minimization)."""
        solution = create_solution(obj_values=[10.0, 8.0, 15.0], sense=Sense.Min)
        result = BestSolutionFound().run(solution, mock_feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == 2.0  # 8.0 / 4.0

    @pytest.mark.parametrize("mock_feature_results", [20.0], indirect=True)
    def test_optimal_solution_maximization(self, mock_feature_results: MagicMock) -> None:
        """Test BSF = 1.0 when best found equals optimal (maximization)."""
        solution = create_solution(obj_values=[10.0, 20.0, 15.0], sense=Sense.Max)
        result = BestSolutionFound().run(solution, mock_feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == 1.0

    @pytest.mark.parametrize("mock_feature_results", [30.0], indirect=True)
    def test_suboptimal_solution_maximization(self, mock_feature_results: MagicMock) -> None:
        """Test BSF > 1.0 when best found is worse than optimal (maximization)."""
        solution = create_solution(obj_values=[10.0, 15.0, 12.0], sense=Sense.Max)

        result = BestSolutionFound().run(solution, mock_feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == 2.0  # 30.0 / 15.0

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_empty_solution(self, mock_feature_results: MagicMock) -> None:
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

        result = BestSolutionFound().run(solution, mock_feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == float("inf")

    @pytest.mark.parametrize("mock_feature_results", [0.0], indirect=True)
    def test_division_by_zero_raises_error(self, mock_feature_results: MagicMock) -> None:
        """Test that division by zero (optimal = 0) raises ZeroDivisionError."""
        solution = create_solution(obj_values=[10.0, 5.0], sense=Sense.Min)

        metric = BestSolutionFound()

        with pytest.raises(ZeroDivisionError, match="dividing by 0"):
            metric.run(solution, mock_feature_results)

    @pytest.mark.parametrize("mock_feature_results", [0.0001], indirect=True)
    def test_custom_tolerance(self, mock_feature_results: MagicMock) -> None:
        """Test that custom absolute tolerance is respected."""
        solution = create_solution(obj_values=[10.0, 5.0], sense=Sense.Min)

        # With default tolerance (1e-3), this should raise
        metric_default = BestSolutionFound()
        with pytest.raises(ZeroDivisionError):
            metric_default.run(solution, mock_feature_results)

        # With smaller tolerance, it should work
        metric_small_tol = BestSolutionFound(abs_tol=1e-6)
        result = metric_small_tol.run(solution, mock_feature_results)
        assert result.best_solution_found == 5.0 / 0.0001

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_none_solution_raises_value_error(self, mock_feature_results: MagicMock) -> None:
        """Test that passing None as solution raises ValueError."""
        metric = BestSolutionFound()

        with pytest.raises(ValueError, match="Solution must not be None"):
            metric.run(None, mock_feature_results)  # type: ignore[arg-type]

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_best_returns_none(self, mock_feature_results: MagicMock) -> None:
        """Test that BSF returns inf when solution.best() returns None."""
        solution = MagicMock(spec=Solution)
        solution.samples = [MagicMock()]
        solution.best.return_value = None

        result = BestSolutionFound().run(solution, mock_feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == float("inf")

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_best_obj_value_is_none(self, mock_feature_results: MagicMock) -> None:
        """Test that BSF returns inf when best sample has obj_value=None."""
        best_sample = MagicMock()
        type(best_sample).obj_value = PropertyMock(return_value=None)

        solution = MagicMock(spec=Solution)
        solution.samples = [best_sample]
        solution.best.return_value = best_sample

        result = BestSolutionFound().run(solution, mock_feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == float("inf")
