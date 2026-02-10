"""Tests for the FractionOfOverallBestSolution metric."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest
from luna_quantum import Sense, Solution, Timer, Vtype
from pydantic import ValidationError

from luna_bench.components.metrics.fraction_of_overall_best_solution import (
    FractionOfOverallBestSolution,
    FractionOfOverallBestSolutionResult,
)
from tests.unit.fixtures import create_solution

if TYPE_CHECKING:
    from unittest.mock import MagicMock


class TestFractionOfOverallBestSolutionResult:
    """Tests for FractionOfOverallBestSolutionResult validation."""

    def test_valid_result_zero(self) -> None:
        """Test that a FOB of 0.0 (no optimal samples) is valid."""
        result = FractionOfOverallBestSolutionResult(fraction_of_overall_best_solution=0.0)
        assert result.fraction_of_overall_best_solution == 0.0

    def test_valid_result_one(self) -> None:
        """Test that a FOB of 1.0 (all optimal samples) is valid."""
        result = FractionOfOverallBestSolutionResult(fraction_of_overall_best_solution=1.0)
        assert result.fraction_of_overall_best_solution == 1.0

    def test_valid_result_partial(self) -> None:
        """Test that a FOB between 0 and 1 is valid."""
        result = FractionOfOverallBestSolutionResult(fraction_of_overall_best_solution=0.5)
        assert result.fraction_of_overall_best_solution == 0.5

    def test_invalid_result_negative(self) -> None:
        """Test that FOB < 0 raises an error."""
        with pytest.raises(ValidationError):
            FractionOfOverallBestSolutionResult(fraction_of_overall_best_solution=-0.1)

    def test_invalid_result_greater_than_one(self) -> None:
        """Test that FOB > 1.0 raises an error."""
        with pytest.raises(ValidationError):
            FractionOfOverallBestSolutionResult(fraction_of_overall_best_solution=1.1)


class TestFractionOfOverallBestSolution:
    """Tests for the FractionOfOverallBestSolution metric."""

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_all_optimal_minimization(self, mock_feature_results: MagicMock) -> None:
        """Test FOB = 1.0 when all samples equal optimal (minimization)."""
        solution = create_solution(obj_values=[5.0, 5.0, 5.0], sense=Sense.Min)

        metric = FractionOfOverallBestSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 1.0

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_some_optimal_minimization(self, mock_feature_results: MagicMock) -> None:
        """Test FOB when some samples equal optimal (minimization)."""
        solution = create_solution(obj_values=[5.0, 10.0, 5.0, 15.0], sense=Sense.Min)

        metric = FractionOfOverallBestSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 0.5  # 2 out of 4

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_no_optimal_minimization(self, mock_feature_results: MagicMock) -> None:
        """Test FOB = 0.0 when no samples equal optimal (minimization)."""
        solution = create_solution(obj_values=[10.0, 15.0, 20.0], sense=Sense.Min)

        metric = FractionOfOverallBestSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 0.0

    @pytest.mark.parametrize("mock_feature_results", [20.0], indirect=True)
    def test_all_optimal_maximization(self, mock_feature_results: MagicMock) -> None:
        """Test FOB = 1.0 when all samples equal optimal (maximization)."""
        solution = create_solution(obj_values=[20.0, 20.0, 20.0], sense=Sense.Max)

        metric = FractionOfOverallBestSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 1.0

    @pytest.mark.parametrize("mock_feature_results", [20.0], indirect=True)
    def test_some_optimal_maximization(self, mock_feature_results: MagicMock) -> None:
        """Test FOB when some samples equal optimal (maximization)."""
        solution = create_solution(obj_values=[20.0, 10.0, 20.0, 5.0], sense=Sense.Max)

        metric = FractionOfOverallBestSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 0.5  # 2 out of 4

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_empty_solution(self, mock_feature_results: MagicMock) -> None:
        """Test that empty solution returns 0.0."""
        timer = Timer.start()
        time.sleep(0.01)
        timing = timer.stop()

        solution = Solution._build(  # type: ignore[attr-defined]
            component_types=[Vtype.Binary],
            binary_cols=[[]],
            timing=timing,
            sense=Sense.Min,
        )

        metric = FractionOfOverallBestSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 0.0

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_no_feasible_samples(self, mock_feature_results: MagicMock) -> None:
        """Test that solution with no feasible samples returns 0.0."""
        solution = create_solution(
            obj_values=[5.0, 5.0, 5.0],
            sense=Sense.Min,
            feasible=[False, False, False],
        )

        metric = FractionOfOverallBestSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 0.0

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_mixed_feasibility(self, mock_feature_results: MagicMock) -> None:
        """Test FOB with mixed feasible/infeasible samples."""
        # 4 samples: 2 feasible optimal, 1 feasible non-optimal, 1 infeasible optimal
        solution = create_solution(
            obj_values=[5.0, 5.0, 10.0, 5.0],
            sense=Sense.Min,
            feasible=[True, True, True, False],
        )

        metric = FractionOfOverallBestSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        # 2 feasible optimal out of 4 total samples
        assert result.fraction_of_overall_best_solution == 0.5

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_custom_tolerance(self, mock_feature_results: MagicMock) -> None:
        """Test that custom absolute tolerance is respected."""
        solution = create_solution(obj_values=[5.0001, 5.0002, 10.0], sense=Sense.Min)

        # With default tolerance (1e-6), values should not match
        metric_default = FractionOfOverallBestSolution()
        result_default = metric_default.run(solution, mock_feature_results)
        assert result_default.fraction_of_overall_best_solution == 0.0

        # With larger tolerance, values should match
        metric_large_tol = FractionOfOverallBestSolution(abs_tol=1e-3)
        result_large_tol = metric_large_tol.run(solution, mock_feature_results)
        assert result_large_tol.fraction_of_overall_best_solution == pytest.approx(2 / 3)

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_single_sample_optimal(self, mock_feature_results: MagicMock) -> None:
        """Test FOB with single optimal sample."""
        solution = create_solution(obj_values=[5.0], sense=Sense.Min)

        metric = FractionOfOverallBestSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 1.0

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_single_sample_not_optimal(self, mock_feature_results: MagicMock) -> None:
        """Test FOB with single non-optimal sample."""
        solution = create_solution(obj_values=[10.0], sense=Sense.Min)

        metric = FractionOfOverallBestSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 0.0
