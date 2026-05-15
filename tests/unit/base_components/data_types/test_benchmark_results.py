from typing import Any
from unittest.mock import MagicMock

from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer


class TestBenchmarkResults:
    """Test BenchmarkResults class."""

    def test_initialization(self) -> None:
        """Test BenchmarkResults initialization with various data."""
        results = BenchmarkResultContainer.model_construct(features={}, metrics={})
        assert results.features == {}
        assert results.metrics == {}

        feature_results: Any = MagicMock()
        metric_results: Any = MagicMock()
        features: dict[str, Any] = {"model1": feature_results}
        metrics: dict[str, dict[str, Any]] = {"model1": {"algo1": metric_results}}
        results = BenchmarkResultContainer.model_construct(features=features, metrics=metrics)
        assert results.features == features
        assert results.metrics == metrics

    def test_get_all_metrics(self) -> None:
        """Test get_all_metrics across various structures."""
        results = BenchmarkResultContainer.model_construct(features={}, metrics={})
        assert list(results.get_all_metrics()) == []

        mr1: Any = MagicMock()
        metrics: dict[str, dict[str, Any]] = {"model1": {"algo1": mr1}}
        results = BenchmarkResultContainer.model_construct(features={}, metrics=metrics)
        metric_list: list[Any] = list(results.get_all_metrics())
        assert len(metric_list) == 1
        assert metric_list[0] == ("model1", "algo1", mr1)

        mr2: Any = MagicMock()
        mr3: Any = MagicMock()
        metrics = {
            "model1": {"algo1": mr1, "algo2": mr2},
            "model2": {"algo1": mr3},
        }
        results = BenchmarkResultContainer.model_construct(features={}, metrics=metrics)
        metric_list = list(results.get_all_metrics())
        assert len(metric_list) == 3
        assert ("model1", "algo1", mr1) in metric_list
        assert ("model1", "algo2", mr2) in metric_list
        assert ("model2", "algo1", mr3) in metric_list

    def test_get_all_metrics_of_type(self) -> None:
        """Test get_all_metrics_of_type filtering."""
        results = BenchmarkResultContainer.model_construct(features={}, metrics={})
        metric_cls: Any = MagicMock()
        assert list(results.get_all_metrics_of_type(metric_cls)) == []

        mr: Any = MagicMock()
        metric_results_container: Any = MagicMock()
        metric_results_container.get_all.return_value = {"metric1": mr}
        metrics: dict[str, dict[str, Any]] = {"model1": {"algo1": metric_results_container}}
        results = BenchmarkResultContainer.model_construct(features={}, metrics=metrics)
        metric_list = list(results.get_all_metrics_of_type(metric_cls))
        assert len(metric_list) == 1
        assert metric_list[0] == ("model1", "algo1", mr)

        mr2: Any = MagicMock()
        mr3: Any = MagicMock()
        mr1_container: Any = MagicMock()
        mr1_container.get_all.return_value = {"metric1": mr}
        mr2_container: Any = MagicMock()
        mr2_container.get_all.return_value = {"metric2": mr2}
        mr3_container: Any = MagicMock()
        mr3_container.get_all.return_value = {"metric3": mr3}
        metrics = {
            "model1": {"algo1": mr1_container, "algo2": mr2_container},
            "model2": {"algo1": mr3_container},
        }
        results = BenchmarkResultContainer.model_construct(features={}, metrics=metrics)
        metric_list = list(results.get_all_metrics_of_type(metric_cls))
        assert len(metric_list) == 3
        assert ("model1", "algo1", mr) in metric_list
        assert ("model1", "algo2", mr2) in metric_list
        assert ("model2", "algo1", mr3) in metric_list

    def test_model_config_allows_arbitrary_types(self) -> None:
        """Test that BenchmarkResults allows arbitrary types."""
        feature_results: Any = MagicMock()
        metric_results: Any = MagicMock()
        result = BenchmarkResultContainer.model_construct(
            features={"model1": feature_results},
            metrics={"model1": {"algo1": metric_results}},
        )
        assert result.features["model1"] == feature_results
        assert result.metrics["model1"]["algo1"] == metric_results

    def test_features_and_metrics_independence(self) -> None:
        """Test that features and metrics are independent."""
        feature1: Any = MagicMock()
        metric1: Any = MagicMock()
        results = BenchmarkResultContainer.model_construct(
            features={"model1": feature1},
            metrics={"model1": {"algo1": metric1}},
        )
        assert results.features["model1"] == feature1
        assert results.metrics["model1"]["algo1"] == metric1

        feature2: Any = MagicMock()
        results.features["model2"] = feature2
        assert "model2" not in results.metrics

    def test_generator_behavior(self) -> None:
        """Test that get_all_metrics and get_all_metrics_of_type return generators."""
        mr1: Any = MagicMock()
        metrics: dict[str, dict[str, Any]] = {"model1": {"algo1": mr1}}
        results = BenchmarkResultContainer.model_construct(features={}, metrics=metrics)

        gen1: Any = results.get_all_metrics()
        assert hasattr(gen1, "__iter__")
        assert hasattr(gen1, "__next__")

        metric_cls: Any = MagicMock()
        metric_results_container: Any = MagicMock()
        metric_results_container.get_all.return_value = {"metric1": mr1}
        metrics = {"model1": {"algo1": metric_results_container}}
        results = BenchmarkResultContainer.model_construct(features={}, metrics=metrics)
        gen2: Any = results.get_all_metrics_of_type(metric_cls)
        assert hasattr(gen2, "__iter__")
        assert hasattr(gen2, "__next__")

    def test_complex_model_structure(self) -> None:
        """Test with complex model and algorithm structure."""
        metric_results: dict[str, dict[str, Any]] = {}
        for m in range(3):
            model_name = f"model{m}"
            for a in range(2):
                algo_name = f"algo{a}"
                mock_result: Any = MagicMock()
                metric_results.setdefault(model_name, {})[algo_name] = mock_result

        results = BenchmarkResultContainer.model_construct(features={}, metrics=metric_results)
        metric_list = list(results.get_all_metrics())
        assert len(metric_list) == 6

    def test_features_only(self) -> None:
        """Test with features but no metrics."""
        feature1: Any = MagicMock()
        feature2: Any = MagicMock()
        features: dict[str, Any] = {"model1": feature1, "model2": feature2}
        results = BenchmarkResultContainer.model_construct(features=features, metrics={})
        assert len(results.features) == 2
        assert results.features["model1"] == feature1
        assert results.features["model2"] == feature2
        assert len(results.metrics) == 0

    def test_metrics_only(self) -> None:
        """Test with metrics but no features."""
        mr1: Any = MagicMock()
        mr2: Any = MagicMock()
        metrics: dict[str, dict[str, Any]] = {
            "model1": {"algo1": mr1},
            "model2": {"algo1": mr2},
        }
        results = BenchmarkResultContainer.model_construct(features={}, metrics=metrics)
        assert len(results.features) == 0
        assert len(results.metrics) == 2
        metric_list = list(results.get_all_metrics())
        assert len(metric_list) == 2
