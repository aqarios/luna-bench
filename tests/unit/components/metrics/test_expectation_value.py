"""Tests for the ExpectationValue metric."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from luna_model import Sense, ValueSource

from luna_bench.custom import MetricDirection
from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer
from luna_bench.metrics.expectation_value import ExpectationValue, ExpectationValueResult

if TYPE_CHECKING:
    from unittest.mock import MagicMock

    from tests.unit.fixtures.mock_feature_results import SolutionFactory


def _create_empty_feature_results() -> FeatureResultContainer:
    """Create empty FeatureResults (ExpectationValue doesn't need features)."""
    return FeatureResultContainer(data={})


class TestExpectationValueResult:
    """Tests for ExpectationValueResult."""

    def test_valid_result(self) -> None:
        """Test that ExpectationValueResult stores the expectation value correctly."""
        result = ExpectationValueResult(expectation_value=1.5)
        assert result.expectation_value == 1.5

    def test_negative_expectation_value(self) -> None:
        """Test that a negative expectation value is valid."""
        result = ExpectationValueResult(expectation_value=-2.5)
        assert result.expectation_value == -2.5


class TestExpectationValue:
    """Tests for the ExpectationValue metric."""

    def test_averages_objective_values(self, create_solution: SolutionFactory) -> None:
        """Test that the metric averages the objective values of all samples."""
        solution = create_solution(obj_values=[1.0, 2.0, 3.0], feasible=[True, True, True])

        result = ExpectationValue().run(solution, _create_empty_feature_results())

        assert isinstance(result, ExpectationValueResult)
        assert result.expectation_value == pytest.approx(2.0)

    def test_single_sample(self, create_solution: SolutionFactory) -> None:
        """Test that a single sample yields its own objective value."""
        solution = create_solution(obj_values=[4.2], feasible=[True])

        result = ExpectationValue().run(solution, _create_empty_feature_results())

        assert result.expectation_value == pytest.approx(4.2)

    @pytest.mark.parametrize("mock_solution_config", [(Sense.MIN, 7.5)], indirect=True)
    def test_uses_solution_expectation_value(
        self, mock_solution_config: MagicMock, mock_feature_results: MagicMock
    ) -> None:
        """Test that the metric delegates to Solution.expectation_value."""
        result = ExpectationValue().run(mock_solution_config, mock_feature_results)

        assert isinstance(result, ExpectationValueResult)
        assert result.expectation_value == 7.5
        mock_solution_config.expectation_value.assert_called_once()

    def test_direction_depends_on_the_problem(self) -> None:
        """Test that the metric flags its direction as depending on the problem sense."""
        assert ExpectationValue.direction is MetricDirection.DEPENDS_ON_SENSE

    def test_direction_is_not_a_field(self) -> None:
        """Test that the direction is class metadata rather than a constructor option."""
        assert "direction" not in ExpectationValue.model_fields

    def test_defaults_to_objective_value_source(self) -> None:
        """Test that the objective values are averaged unless configured otherwise."""
        assert ExpectationValue().value_source == ValueSource.OBJ

    @pytest.mark.parametrize("value_source", [ValueSource.OBJ, ValueSource.RAW])
    @pytest.mark.parametrize("mock_solution_config", [(Sense.MIN, 7.5)], indirect=True)
    def test_forwards_value_source(
        self, value_source: ValueSource, mock_solution_config: MagicMock, mock_feature_results: MagicMock
    ) -> None:
        """Test that the configured value source is passed on to the solution."""
        ExpectationValue(value_source=value_source).run(mock_solution_config, mock_feature_results)

        mock_solution_config.expectation_value.assert_called_once_with(value_toggle=value_source)
