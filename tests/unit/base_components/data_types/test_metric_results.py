"""Tests for MetricResults data type."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from luna_bench.custom.result_containers.metric_result_container import MetricResultContainer
from luna_bench.errors.components.metrics.metric_result_unknown_name_error import (
    MetricResulUnknownNameError,
)
from luna_bench.errors.components.metrics.metric_result_wrong_class_error import (
    MetricResultWrongClassError,
)


class TestMetricResults:
    """Test MetricResults class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.metric_cls1: Any = MagicMock()
        self.metric_cls1.__name__ = "MetricClass1"
        self.metric_cls2: Any = MagicMock()
        self.metric_cls2.__name__ = "MetricClass2"
        self.metric_result1: Any = MagicMock()
        self.metric_result2: Any = MagicMock()
        self.metric_config1: Any = MagicMock()
        self.metric_config2: Any = MagicMock()

    def _build_data(self, metric_cls: Any, metrics: dict[str, Any]) -> MetricResultContainer:  # noqa: ANN401
        """Build MetricResults with given class and metrics."""
        data: dict[Any, dict[str, Any]] = {metric_cls: metrics}
        return MetricResultContainer.model_construct(data=data)

    def test_initialization_with_empty_data(self) -> None:
        """Test MetricResults initialization with empty data."""
        data: dict[Any, Any] = {}
        results = MetricResultContainer.model_construct(data=data)
        assert results.data == data

    def test_initialization_with_data(self) -> None:
        """Test MetricResults initialization with data."""
        data: dict[Any, dict[str, Any]] = {
            self.metric_cls1: {
                "metric1": (self.metric_result1, self.metric_config1),
                "metric2": (self.metric_result2, self.metric_config2),
            }
        }
        results = MetricResultContainer.model_construct(data=data)
        assert results.data == data

    def test_get_all_methods(self) -> None:
        """Test get_all and get_all_with_config with valid class."""
        data: dict[Any, dict[str, Any]] = {
            self.metric_cls1: {
                "metric1": (self.metric_result1, self.metric_config1),
                "metric2": (self.metric_result2, self.metric_config2),
            }
        }
        results = MetricResultContainer.model_construct(data=data)

        all_with_config: Any = results.get_all_with_config(self.metric_cls1)
        assert all_with_config["metric1"] == (self.metric_result1, self.metric_config1)
        assert all_with_config["metric2"] == (self.metric_result2, self.metric_config2)

        all_results: Any = results.get_all(self.metric_cls1)
        assert all_results["metric1"] == self.metric_result1
        assert all_results["metric2"] == self.metric_result2

    def test_get_all_invalid_class_error(self) -> None:
        """Test get_all/get_all_with_config raise errors for invalid class."""
        metrics: dict[str, Any] = {"metric1": (self.metric_result1, self.metric_config1)}
        results = self._build_data(self.metric_cls1, metrics)

        with pytest.raises(MetricResultWrongClassError):
            results.get_all_with_config(self.metric_cls2)
        with pytest.raises(MetricResultWrongClassError):
            results.get_all(self.metric_cls2)

    def test_get_methods(self) -> None:
        """Test get and get_with_config methods."""
        metrics: dict[str, Any] = {"metric1": (self.metric_result1, self.metric_config1)}
        results = self._build_data(self.metric_cls1, metrics)

        assert results.get(self.metric_cls1, "metric1") == self.metric_result1

        result: Any
        config: Any
        result, config = results.get_with_config(self.metric_cls1, "metric1")
        assert result == self.metric_result1
        assert config == self.metric_config1

    def test_get_invalid_class_error(self) -> None:
        """Test get/get_with_config raise errors for invalid class."""
        metrics: dict[str, Any] = {"metric1": (self.metric_result1, self.metric_config1)}
        results = self._build_data(self.metric_cls1, metrics)

        with pytest.raises(MetricResultWrongClassError):
            results.get(self.metric_cls2, "metric1")
        with pytest.raises(MetricResultWrongClassError):
            results.get_with_config(self.metric_cls2, "metric1")

    def test_get_invalid_name_error(self) -> None:
        """Test get/get_with_config raise errors for invalid metric name."""
        metrics: dict[str, Any] = {"metric1": (self.metric_result1, self.metric_config1)}
        results = self._build_data(self.metric_cls1, metrics)

        with pytest.raises(MetricResulUnknownNameError):
            results.get(self.metric_cls1, "unknown")
        with pytest.raises(MetricResulUnknownNameError):
            results.get_with_config(self.metric_cls1, "unknown")

    def test_first_methods(self) -> None:
        """Test first and first_with_config methods."""
        metrics: dict[str, Any] = {"metric1": (self.metric_result1, self.metric_config1)}
        results = self._build_data(self.metric_cls1, metrics)

        assert results.first(self.metric_cls1) == self.metric_result1

        result: Any
        config: Any
        result, config = results.first_with_config(self.metric_cls1)
        assert result == self.metric_result1
        assert config == self.metric_config1

    def test_first_invalid_class_error(self) -> None:
        """Test first/first_with_config raise errors for invalid class."""
        metrics: dict[str, Any] = {"metric1": (self.metric_result1, self.metric_config1)}
        results = self._build_data(self.metric_cls1, metrics)

        with pytest.raises(MetricResultWrongClassError):
            results.first(self.metric_cls2)
        with pytest.raises(MetricResultWrongClassError):
            results.first_with_config(self.metric_cls2)

    def test_multiple_metrics(self) -> None:
        """Test with multiple metrics and multiple classes."""
        metric_result3: Any = MagicMock()
        metric_config3: Any = MagicMock()
        data: dict[Any, dict[str, Any]] = {
            self.metric_cls1: {
                "metric1": (self.metric_result1, self.metric_config1),
                "metric2": (self.metric_result2, self.metric_config2),
                "metric3": (metric_result3, metric_config3),
            },
            self.metric_cls2: {
                "metric_a": (self.metric_result1, self.metric_config1),
            },
        }
        results = MetricResultContainer.model_construct(data=data)

        all1: Any = results.get_all(self.metric_cls1)
        assert len(all1) == 3
        assert all1["metric1"] == self.metric_result1

        all2: Any = results.get_all(self.metric_cls2)
        assert len(all2) == 1
        assert all2["metric_a"] == self.metric_result1

    def test_model_config_arbitrary_types(self) -> None:
        """Test that MetricResults allows arbitrary types."""
        data: dict[Any, dict[str, Any]] = {
            object(): {
                "metric1": (self.metric_result1, self.metric_config1),
            }
        }
        results = MetricResultContainer.model_construct(data=data)
        assert len(results.data) == 1

    def test_consistency_get_variants(self) -> None:
        """Test consistency between get and get_with_config."""
        metrics: dict[str, Any] = {"metric1": (self.metric_result1, self.metric_config1)}
        results = self._build_data(self.metric_cls1, metrics)

        result: Any = results.get(self.metric_cls1, "metric1")
        result_with_cfg: Any
        cfg: Any
        result_with_cfg, cfg = results.get_with_config(self.metric_cls1, "metric1")
        assert result == result_with_cfg
        assert cfg == self.metric_config1

    def test_consistency_first_variants(self) -> None:
        """Test consistency between first and first_with_config."""
        metrics: dict[str, Any] = {"metric1": (self.metric_result1, self.metric_config1)}
        results = self._build_data(self.metric_cls1, metrics)

        first: Any = results.first(self.metric_cls1)
        first_with_cfg: Any
        cfg: Any
        first_with_cfg, cfg = results.first_with_config(self.metric_cls1)
        assert first == first_with_cfg
        assert cfg == self.metric_config1

    def test_large_metric_set(self) -> None:
        """Test with many metrics."""
        metrics: dict[str, Any] = {f"m{i}": (MagicMock(), MagicMock()) for i in range(20)}
        results = self._build_data(self.metric_cls1, metrics)
        all_results: Any = results.get_all(self.metric_cls1)
        assert len(all_results) == 20
        for i in range(20):
            assert f"m{i}" in all_results

    def test_get_all_with_config_returns_tuples(self) -> None:
        """Test get_all_with_config returns tuples with results and configs."""
        metrics: dict[str, Any] = {
            "m1": (self.metric_result1, self.metric_config1),
            "m2": (self.metric_result2, self.metric_config2),
        }
        results = self._build_data(self.metric_cls1, metrics)
        all_with_cfg: Any = results.get_all_with_config(self.metric_cls1)
        assert all_with_cfg["m1"][1] == self.metric_config1
        assert all_with_cfg["m2"][1] == self.metric_config2

    def test_first_with_multiple_options(self) -> None:
        """Test first returns one value from multiple metrics."""
        metric_result3: Any = MagicMock()
        metric_config3: Any = MagicMock()
        metrics: dict[str, Any] = {
            "m1": (self.metric_result1, self.metric_config1),
            "m2": (self.metric_result2, self.metric_config2),
            "m3": (metric_result3, metric_config3),
        }
        results = self._build_data(self.metric_cls1, metrics)

        first_result: Any = results.first(self.metric_cls1)
        assert first_result in [self.metric_result1, self.metric_result2, metric_result3]

        first_val: Any
        first_cfg: Any
        first_val, first_cfg = results.first_with_config(self.metric_cls1)
        assert first_val in [self.metric_result1, self.metric_result2, metric_result3]
        assert first_cfg in [
            self.metric_config1,
            self.metric_config2,
            metric_config3,
        ]

    def test_error_on_wrong_class_from_get_all(self) -> None:
        """Test error for wrong class from get_all provides context."""
        metrics: dict[str, Any] = {"metric1": (self.metric_result1, self.metric_config1)}
        results = self._build_data(self.metric_cls1, metrics)

        with pytest.raises(MetricResultWrongClassError):
            results.get_all(self.metric_cls2)

    def test_error_on_unknown_name_from_get(self) -> None:
        """Test error for unknown name from get provides context."""
        metrics: dict[str, Any] = {"metric1": (self.metric_result1, self.metric_config1)}
        results = self._build_data(self.metric_cls1, metrics)

        with pytest.raises(MetricResulUnknownNameError):
            results.get(self.metric_cls1, "nonexistent")

    def test_all_classes_in_data(self) -> None:
        """Test accessing all available metric classes."""
        data: dict[Any, dict[str, Any]] = {
            self.metric_cls1: {
                "m1": (self.metric_result1, self.metric_config1),
            },
            self.metric_cls2: {
                "m2": (self.metric_result2, self.metric_config2),
            },
        }
        results = MetricResultContainer.model_construct(data=data)
        assert len(results.data) == 2
        assert self.metric_cls1 in results.data
        assert self.metric_cls2 in results.data
