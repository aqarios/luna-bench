"""Tests for MetricDirection and the direction declared by each built-in metric."""

from __future__ import annotations

from typing import Any

import pytest

from luna_bench.custom import BaseMetric, MetricDirection
from luna_bench.metrics import (
    ApproximationRatio,
    BestSolutionFound,
    BestSolutionFoundRatio,
    ExpectationValue,
    FakeMetric,
    FeasibilityRatio,
    FeasibleSamples,
    FractionOfOverallBestSolution,
    Runtime,
    TimeToSolution,
)


class TestMetricDirection:
    """Tests for the MetricDirection enum."""

    def test_members(self) -> None:
        """Test the two absolute directions plus DEPENDS_ON_SENSE and INDIFFERENT are offered.

        DEPENDS_ON_SENSE and INDIFFERENT are separate states on purpose: the first says
        there is a better value but the metric alone cannot say which, the second that the
        question does not apply.
        """
        assert set(MetricDirection) == {
            MetricDirection.HIGHER_IS_BETTER,
            MetricDirection.LOWER_IS_BETTER,
            MetricDirection.DEPENDS_ON_SENSE,
            MetricDirection.INDIFFERENT,
        }

    @pytest.mark.parametrize("direction", list(MetricDirection))
    def test_is_a_string(self, direction: MetricDirection) -> None:
        """Test that directions serialize as strings, like the project's other enums."""
        assert isinstance(direction.value, str)
        assert MetricDirection(str(direction)) is direction


class TestBaseMetricDirection:
    """Tests for the direction declared on metric classes."""

    def test_defaults_to_indifferent(self) -> None:
        """Test that a metric declaring no direction is treated as having none."""
        assert BaseMetric.direction is MetricDirection.INDIFFERENT
        assert FakeMetric.direction is MetricDirection.INDIFFERENT

    @pytest.mark.parametrize(
        ("metric_cls", "expected"),
        [
            (ApproximationRatio, MetricDirection.HIGHER_IS_BETTER),
            (FeasibilityRatio, MetricDirection.HIGHER_IS_BETTER),
            (FractionOfOverallBestSolution, MetricDirection.HIGHER_IS_BETTER),
            (BestSolutionFoundRatio, MetricDirection.LOWER_IS_BETTER),
            (Runtime, MetricDirection.LOWER_IS_BETTER),
            (TimeToSolution, MetricDirection.LOWER_IS_BETTER),
            (BestSolutionFound, MetricDirection.DEPENDS_ON_SENSE),
            (ExpectationValue, MetricDirection.DEPENDS_ON_SENSE),
            (FeasibleSamples, MetricDirection.INDIFFERENT),
        ],
    )
    def test_builtin_metric_directions(self, metric_cls: type[BaseMetric[Any]], expected: MetricDirection) -> None:
        """Test that every built-in metric declares the direction of its scale."""
        assert metric_cls.direction is expected

    @pytest.mark.parametrize(
        "metric_cls",
        [
            ApproximationRatio,
            BestSolutionFound,
            BestSolutionFoundRatio,
            ExpectationValue,
            FeasibilityRatio,
            FeasibleSamples,
            FractionOfOverallBestSolution,
            Runtime,
            TimeToSolution,
        ],
    )
    def test_direction_is_class_metadata(self, metric_cls: type[BaseMetric[Any]]) -> None:
        """Test that the direction stays off the constructor and out of the metric params."""
        assert "direction" not in metric_cls.model_fields
