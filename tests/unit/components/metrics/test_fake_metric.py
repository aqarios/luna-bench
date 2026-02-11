"""Tests for the FakeMetric."""

from __future__ import annotations

from unittest.mock import MagicMock

from luna_quantum import Solution

from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.components.metrics.fake_metric import FakeMetric, FakeMetricResult


class TestFakeMetric:
    """Tests for the FakeMetric."""

    def test_run_returns_fake_metric_result(self) -> None:
        """Test that FakeMetric.run returns a FakeMetricResult with a random number."""
        solution = MagicMock(spec=Solution)
        feature_results = MagicMock(spec=FeatureResults)

        metric = FakeMetric()
        result = metric.run(solution, feature_results)

        assert isinstance(result, FakeMetricResult)
        assert 0 <= result.random_number <= 100
