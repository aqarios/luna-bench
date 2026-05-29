"""Tests for the BestSolutionFound metric."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest
from luna_model import Sense, Solution
from luna_model.solution import ValueSource

from luna_bench.metrics.best_solution_found import (
    BestSolutionFound,
    BestSolutionFoundResult,
)

if TYPE_CHECKING:
    from tests.unit.fixtures.mock_feature_results import SolutionFactory


class TestBestSolutionFoundResult:
    """Tests for BestSolutionFoundResult validation."""

    def test_accepts_finite_value(self) -> None:
        """Test that a finite objective value is stored."""
        result = BestSolutionFoundResult(best_solution_found=5.0)
        assert result.best_solution_found == 5.0

    def test_accepts_infinity(self) -> None:
        """Test that infinity is valid (no feasible solution found)."""
        result = BestSolutionFoundResult(best_solution_found=float("inf"))
        assert result.best_solution_found == float("inf")

    def test_accepts_negative_value(self) -> None:
        """Unlike the ratio metric, raw objective values may be negative."""
        result = BestSolutionFoundResult(best_solution_found=-3.5)
        assert result.best_solution_found == -3.5


class TestBestSolutionFound:
    """Tests for the BestSolutionFound metric."""

    def test_best_feasible_minimization(
        self, create_solution: SolutionFactory, mock_feature_results: MagicMock
    ) -> None:
        """Test the lowest feasible objective value is returned (minimization)."""
        solution = create_solution(obj_values=[10.0, 5.0, 15.0], sense=Sense.MIN, feasible=[True, True, True])
        result = BestSolutionFound().run(solution, mock_feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == 5.0

    def test_best_feasible_maximization(
        self, create_solution: SolutionFactory, mock_feature_results: MagicMock
    ) -> None:
        """Test the highest feasible objective value is returned (maximization)."""
        solution = create_solution(obj_values=[10.0, 20.0, 15.0], sense=Sense.MAX, feasible=[True, True, True])
        result = BestSolutionFound().run(solution, mock_feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == 20.0

    def test_ignores_infeasible_minimization(
        self, create_solution: SolutionFactory, mock_feature_results: MagicMock
    ) -> None:
        """Test that infeasible samples are excluded (minimization)."""
        # The lowest value (5.0) is infeasible, so the best feasible value is 10.0.
        solution = create_solution(obj_values=[10.0, 5.0, 15.0], sense=Sense.MIN, feasible=[True, False, True])
        result = BestSolutionFound().run(solution, mock_feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == 10.0

    def test_ignores_infeasible_maximization(
        self, create_solution: SolutionFactory, mock_feature_results: MagicMock
    ) -> None:
        """Test that infeasible samples are excluded (maximization)."""
        # The highest value (20.0) is infeasible, so the best feasible value is 15.0.
        solution = create_solution(obj_values=[10.0, 20.0, 15.0], sense=Sense.MAX, feasible=[True, False, True])
        result = BestSolutionFound().run(solution, mock_feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == 15.0

    def test_no_feasible_solution_returns_inf(
        self, create_solution: SolutionFactory, mock_feature_results: MagicMock
    ) -> None:
        """Test that inf is returned when no sample is feasible."""
        solution = create_solution(obj_values=[10.0, 5.0], sense=Sense.MIN, feasible=[False, False])
        result = BestSolutionFound().run(solution, mock_feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == float("inf")

    def test_best_returns_none_returns_inf(self, mock_feature_results: MagicMock) -> None:
        """Test that inf is returned when best() returns None (no feasible result)."""
        solution = MagicMock(spec=Solution)
        solution.best.return_value = None

        result = BestSolutionFound().run(solution, mock_feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == float("inf")

    def test_value_is_none_returns_inf(self, mock_feature_results: MagicMock) -> None:
        """Test that inf is returned when the best sample has obj_value=None."""
        best_view = MagicMock()
        best_view.obj_value = None

        solution = MagicMock(spec=Solution)
        solution.best.return_value = [best_view]

        result = BestSolutionFound().run(solution, mock_feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == float("inf")

    def test_value_source_raw_energy(self, mock_feature_results: MagicMock) -> None:
        """Test that ValueSource.RAW reads the raw energy instead of the objective."""
        best_view = MagicMock()
        best_view.obj_value = 5.0
        best_view.raw_energy = 2.0

        solution = MagicMock(spec=Solution)
        solution.best.return_value = [best_view]

        result = BestSolutionFound(value_source=ValueSource.RAW).run(solution, mock_feature_results)

        assert isinstance(result, BestSolutionFoundResult)
        assert result.best_solution_found == 2.0

    def test_none_solution_raises_value_error(self, mock_feature_results: MagicMock) -> None:
        """Test that passing None as the solution raises ValueError."""
        metric = BestSolutionFound()

        with pytest.raises(ValueError, match="Solution must not be None"):
            metric.run(None, mock_feature_results)  # type: ignore[arg-type]
