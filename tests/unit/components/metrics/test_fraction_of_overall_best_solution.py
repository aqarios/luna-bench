"""Tests for the FractionOfOverallBestSolution metric."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from luna_model import Sense
from pydantic import ValidationError

from luna_bench.metrics.fraction_of_overall_best_solution import (
    FractionOfOverallBestSolution,
    FractionOfOverallBestSolutionResult,
)

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from tests.unit.fixtures.mock_feature_results import SolutionFactory


class TestFractionOfOverallBestSolutionResult:
    """Tests for FractionOfOverallBestSolutionResult validation."""

    @pytest.mark.parametrize("ratio", [1.0, 0.0, 0.5])
    def test_valid_result(self, ratio: float) -> None:
        """Test that FOB stores the value correctly."""
        result = FractionOfOverallBestSolutionResult(fraction_of_overall_best_solution=ratio)
        assert result.fraction_of_overall_best_solution == ratio

    @pytest.mark.parametrize("ratio", [-0.1, 1.1])
    def test_invalid_result(self, ratio: float) -> None:
        """Test that FOB < 0 or FOB > 1.0 are invlaid."""
        with pytest.raises(ValidationError):
            FractionOfOverallBestSolutionResult(fraction_of_overall_best_solution=ratio)


class TestFractionOfOverallBestSolution:
    """Tests for the FractionOfOverallBestSolution metric."""

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_all_optimal_minimization(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test FOB = 1.0 when all samples equal optimal (minimization)."""
        solution = create_solution(obj_values=[5.0, 5.0, 5.0], sense=Sense.MIN)

        metric = FractionOfOverallBestSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 1.0

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_some_optimal_minimization(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test FOB when some samples equal optimal (minimization)."""
        solution = create_solution(obj_values=[5.0, 10.0, 5.0, 15.0], sense=Sense.MIN)

        result = FractionOfOverallBestSolution().run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 0.5  # 2 out of 4

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_no_optimal_minimization(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test FOB = 0.0 when no samples equal optimal (minimization)."""
        solution = create_solution(obj_values=[10.0, 15.0, 20.0], sense=Sense.MIN)

        result = FractionOfOverallBestSolution().run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 0.0

    @pytest.mark.parametrize("mock_feature_results", [20.0], indirect=True)
    def test_all_optimal_maximization(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test FOB = 1.0 when all samples equal optimal (maximization)."""
        solution = create_solution(obj_values=[20.0, 20.0, 20.0], sense=Sense.MAX)

        result = FractionOfOverallBestSolution().run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 1.0

    @pytest.mark.parametrize("mock_feature_results", [20.0], indirect=True)
    def test_some_optimal_maximization(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test FOB when some samples equal optimal (maximization)."""
        solution = create_solution(obj_values=[20.0, 10.0, 20.0, 5.0], sense=Sense.MAX)

        metric = FractionOfOverallBestSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 0.5  # 2 out of 4

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_empty_solution(self, mock_solution_config: MagicMock, mock_feature_results: MagicMock) -> None:
        """Test that empty solution returns 0.0."""
        result = FractionOfOverallBestSolution().run(mock_solution_config, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 0.0

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_no_feasible_samples(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test that a solution without any feasible samples returns 0.0."""
        solution = create_solution(
            obj_values=[5.0, 5.0, 5.0],
            sense=Sense.MIN,
            feasible=[False, False, False],
        )

        metric = FractionOfOverallBestSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 0.0

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_mixed_feasibility(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test FOB with mixed feasible/infeasible samples."""
        # 4 samples: 2 feasible optimal, 1 feasible non-optimal, 1 infeasible optimal
        solution = create_solution(
            obj_values=[5.0, 5.0, 10.0, 5.0],
            sense=Sense.MIN,
            feasible=[True, True, True, False],
        )

        metric = FractionOfOverallBestSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        # 2 feasible optimal out of 4 total samples
        assert result.fraction_of_overall_best_solution == 0.5

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_custom_tolerance(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test that custom absolute tolerance is respected."""
        solution = create_solution(obj_values=[5.0001, 5.0002, 10.0], sense=Sense.MIN)

        # With default tolerance (1e-6), values should not match
        metric_default = FractionOfOverallBestSolution()
        result_default = metric_default.run(solution, mock_feature_results)
        assert result_default.fraction_of_overall_best_solution == 0.0

        # With larger tolerance, values should match
        metric_large_tol = FractionOfOverallBestSolution(abs_tol=1e-3)
        result_large_tol = metric_large_tol.run(solution, mock_feature_results)
        assert result_large_tol.fraction_of_overall_best_solution == pytest.approx(2 / 3)

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_single_sample_optimal(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test FOB with a single optimal sample."""
        solution = create_solution(obj_values=[5.0], sense=Sense.MIN)

        metric = FractionOfOverallBestSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 1.0

    @pytest.mark.parametrize("mock_feature_results", [5.0], indirect=True)
    def test_single_sample_not_optimal(self, create_solution: SolutionFactory, mock_feature_results: MagicMock) -> None:
        """Test FOB with single non-optimal sample."""
        solution = create_solution(obj_values=[10.0], sense=Sense.MIN)

        metric = FractionOfOverallBestSolution()
        result = metric.run(solution, mock_feature_results)

        assert isinstance(result, FractionOfOverallBestSolutionResult)
        assert result.fraction_of_overall_best_solution == 0.0
