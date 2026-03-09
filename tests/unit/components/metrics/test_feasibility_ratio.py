"""Tests for the FeasibilityRatio metric."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from luna_model import Sense
from pydantic import ValidationError

from luna_bench.components.metrics.feasbility_ratio import FeasibilityRatio, FeasibilityRatioResult

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from tests.unit.fixtures.mock_feature_results import SolutionFactory


class TestFeasibilityRatioResult:
    """Tests for FeasibilityRatioResult."""

    @pytest.mark.parametrize("ratio", [1.0, 0.0, 0.5])
    def test_valid_result(self, ratio: float) -> None:
        """Test that feasibility ratio stores the value correctly."""
        result = FeasibilityRatioResult(feasibility_ratio=ratio)
        assert result.feasibility_ratio == ratio

    @pytest.mark.parametrize("ratio", [-0.1, 1.1])
    def test_invalid_result(self, ratio: float) -> None:
        """Test that FR < 0 or FR > 1.0 are invalid."""
        with pytest.raises(ValidationError):
            FeasibilityRatioResult(feasibility_ratio=ratio)


class TestFeasibilityRatio:
    """Tests for the FeasibilityRatio metric."""

    @pytest.mark.parametrize(
        ("obj_values", "feasible", "sense", "expected_ratio"),
        [
            ([1, 2, 3], [True, True, True], Sense.MIN, 1.0),
            ([1, 2, 3], [False, False, False], Sense.MIN, 0.0),
            ([1, 2, 3, 4], [True, False, True, False], Sense.MIN, 0.5),
            ([1, 2, 3], [True, False, False], Sense.MIN, 1 / 3),
            ([1], [True], Sense.MIN, 1.0),
            ([1], [False], Sense.MIN, 0.0),
            ([1, 2], [True, False], Sense.MAX, 0.5),
        ],
    )
    def test_parametrized_feasibility_ratios(
        self,
        obj_values: list[float],
        feasible: list[bool],
        sense: Sense,
        expected_ratio: float,
        create_solution: SolutionFactory,
        mock_feature_results: MagicMock,
    ) -> None:
        """Parametrized test for various feasibility ratio scenarios."""
        solution = create_solution(obj_values=obj_values, feasible=feasible, sense=sense)
        result = FeasibilityRatio().run(solution, mock_feature_results)

        assert isinstance(result, FeasibilityRatioResult)
        assert result.feasibility_ratio == pytest.approx(expected_ratio)

    def test_empty_solution(self, mock_solution_config: MagicMock, mock_feature_results: MagicMock) -> None:
        """Test that an empty solution returns 0.0."""
        result = FeasibilityRatio().run(mock_solution_config, mock_feature_results)

        assert isinstance(result, FeasibilityRatioResult)
        assert result.feasibility_ratio == 0.0
