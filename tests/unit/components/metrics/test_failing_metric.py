"""Tests for the FailingMetric."""

from __future__ import annotations

import pytest

from luna_bench.components.metrics.failing_metric import FailingMetric


class TestFakeMetric:
    """Tests for the FailingMetric."""

    def test_run_returns_fake_metric_result(self) -> None:
        """Test that FailingMetric.run raises Value Error."""
        metric = FailingMetric()
        with pytest.raises(ValueError, match="Failing Metric because of Value Error"):
            metric.run(None, None)  # type: ignore[arg-type]
