"""Tests for the FakeMetric."""

from __future__ import annotations

from unittest.mock import MagicMock

from luna_model import Solution

from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer
from luna_bench.metrics.fake_metric import FakeMetric, FakeMetricResult


class TestFakeMetric:
    """Tests for the FakeMetric."""

    def test_run_returns_fake_metric_result(self) -> None:
        """Test that FakeMetric.run returns a FakeMetricResult with a random number."""
        solution = MagicMock(spec=Solution)
        feature_results = MagicMock(spec=FeatureResultContainer)

        metric = FakeMetric()
        result = metric.run(solution, feature_results)

        assert isinstance(result, FakeMetricResult)
        assert 0 <= result.random_number <= 100
