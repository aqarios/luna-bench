"""Tests for the FeasibleSamples metric."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from luna_model import Sense
from pydantic import ValidationError

from luna_bench.metrics.feasible_samples import FeasibleSamples, FeasibleSamplesResult

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from tests.unit.fixtures.mock_feature_results import SolutionFactory


class TestFeasibleSamplesResult:
    """Tests for FeasibleSamplesResult."""

    @pytest.mark.parametrize(("num_feasible", "num_samples"), [(0, 0), (0, 5), (3, 5), (5, 5)])
    def test_valid_result(self, num_feasible: int, num_samples: int) -> None:
        """Test that both counts are stored as given."""
        result = FeasibleSamplesResult(num_feasible_samples=num_feasible, num_samples=num_samples)

        assert result.num_feasible_samples == num_feasible
        assert result.num_samples == num_samples

    @pytest.mark.parametrize(("num_feasible", "num_samples"), [(-1, 5), (0, -5)])
    def test_negative_counts_are_invalid(self, num_feasible: int, num_samples: int) -> None:
        """Test that a negative sample count is rejected."""
        with pytest.raises(ValidationError):
            FeasibleSamplesResult(num_feasible_samples=num_feasible, num_samples=num_samples)


class TestFeasibleSamples:
    """Tests for the FeasibleSamples metric."""

    @pytest.mark.parametrize(
        ("obj_values", "feasible", "sense", "expected_feasible", "expected_total"),
        [
            ([1, 2, 3], [True, True, True], Sense.MIN, 3, 3),
            ([1, 2, 3], [False, False, False], Sense.MIN, 0, 3),
            ([1, 2, 3, 4], [True, False, True, False], Sense.MIN, 2, 4),
            ([1], [True], Sense.MIN, 1, 1),
            ([1, 2], [True, False], Sense.MAX, 1, 2),
        ],
    )
    def test_parametrized_sample_counts(
        self,
        obj_values: list[float],
        feasible: list[bool],
        sense: Sense,
        expected_feasible: int,
        expected_total: int,
        create_solution: SolutionFactory,
        mock_feature_results: MagicMock,
    ) -> None:
        """Parametrized test for various feasible and total sample counts."""
        solution = create_solution(obj_values=obj_values, feasible=feasible, sense=sense)

        result = FeasibleSamples().run(solution, mock_feature_results)

        assert isinstance(result, FeasibleSamplesResult)
        assert result.num_feasible_samples == expected_feasible
        assert result.num_samples == expected_total

    def test_empty_solution(self, mock_solution_config: MagicMock, mock_feature_results: MagicMock) -> None:
        """Test that a solution without samples reports zero for both counts."""
        result = FeasibleSamples().run(mock_solution_config, mock_feature_results)

        assert isinstance(result, FeasibleSamplesResult)
        assert result.num_feasible_samples == 0
        assert result.num_samples == 0
