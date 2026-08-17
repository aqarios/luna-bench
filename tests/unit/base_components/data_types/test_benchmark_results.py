from typing import Any
from unittest.mock import MagicMock

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.entities import (
    AlgorithmEntity,
    AlgorithmResultEntity,
    BenchmarkEntity,
    FeatureEntity,
    FeatureResultEntity,
    JobStatus,
    MetricEntity,
)
from tests.unit.fixtures.mock_components import MockAlgorithm, MockFeature, MockMetric
from tests.unit.fixtures.mock_entities import make_algo_entity, make_feature_entity, make_metric_entity


def _make_benchmark(
    features: list[FeatureEntity] | None = None,
    metrics: list[MetricEntity] | None = None,
    algorithms: list[AlgorithmEntity] | None = None,
) -> BenchmarkEntity:
    return BenchmarkEntity(
        name="test_bench",
        modelset=None,
        features=features or [],
        algorithms=algorithms or [],
        metrics=metrics or [],
        plots=[],
    )


class TestFromBenchmark:
    def test_empty_benchmark(self) -> None:
        container = BenchmarkResultContainer.from_benchmark(_make_benchmark())

        assert container.features == {}
        assert container.metrics == {}
        assert container.algorithms == {}

    def test_features_grouped_by_model_and_name(self) -> None:
        feature = make_feature_entity("feat_a", ("model_1", {"count": 42}), ("model_2", {"count": 7}))
        container = BenchmarkResultContainer.from_benchmark(_make_benchmark(features=[feature]))

        assert set(container.features) == {"model_1", "model_2"}
        result, config = container.features["model_1"].get_with_config(MockFeature, "feat_a")
        assert result.model_dump() == {"count": 42}
        assert config is feature.feature

    def test_feature_without_result_is_skipped(self) -> None:
        feature = make_feature_entity("feat_a", ("model_1", {"count": 42}))
        feature.results["model_2"] = FeatureResultEntity(
            processing_time_ms=10,
            model_name="model_2",
            status=JobStatus.FAILED,
            error="boom",
            result=None,
        )
        container = BenchmarkResultContainer.from_benchmark(_make_benchmark(features=[feature]))

        assert set(container.features) == {"model_1"}

    def test_metrics_grouped_by_model_algorithm_and_name(self) -> None:
        metric = make_metric_entity(
            "accuracy",
            ("algo_1", "model_1", {"score": 0.9}),
            ("algo_2", "model_1", {"score": 0.8}),
        )
        container = BenchmarkResultContainer.from_benchmark(_make_benchmark(metrics=[metric]))

        assert set(container.metrics["model_1"]) == {"algo_1", "algo_2"}
        result = container.metrics["model_1"]["algo_1"].get(MockMetric, "accuracy")
        assert result.model_dump() == {"score": 0.9}

    def test_metric_without_result_is_skipped(self) -> None:
        metric = make_metric_entity("accuracy", ("algo_1", "model_1", {}), status=JobStatus.FAILED, error="boom")
        container = BenchmarkResultContainer.from_benchmark(_make_benchmark(metrics=[metric]))

        assert container.metrics == {}

    def test_algorithms_include_failed_runs(self) -> None:
        algo = AlgorithmEntity(
            name="algo_1",
            algorithm=MockAlgorithm(),
            results={
                "model_1": AlgorithmResultEntity(
                    meta_data=ArbitraryDataDomain.model_validate({"runtime": 1.5}),
                    status=JobStatus.FAILED,
                    error="boom",
                    solution=None,
                    task_id=None,
                    retrival_data=None,
                    model_id=1,
                )
            },
        )
        container = BenchmarkResultContainer.from_benchmark(_make_benchmark(algorithms=[algo]))

        run_result = container.algorithms["model_1"]["algo_1"]
        assert run_result.solution is None
        assert run_result.meta_data == {"runtime": 1.5}
        assert run_result.algorithm is algo.algorithm

    def test_multiple_algorithms_and_models(self) -> None:
        algo1 = make_algo_entity("algo_1", ["model_1", "model_2"])
        algo2 = make_algo_entity("algo_2", ["model_1"])
        container = BenchmarkResultContainer.from_benchmark(_make_benchmark(algorithms=[algo1, algo2]))

        assert set(container.algorithms) == {"model_1", "model_2"}
        assert set(container.algorithms["model_1"]) == {"algo_1", "algo_2"}
        assert set(container.algorithms["model_2"]) == {"algo_1"}
        assert list(container.get_all_algorithms()) == [
            ("model_1", "algo_1", container.algorithms["model_1"]["algo_1"]),
            ("model_1", "algo_2", container.algorithms["model_1"]["algo_2"]),
            ("model_2", "algo_1", container.algorithms["model_2"]["algo_1"]),
        ]


class TestBenchmarkResults:
    """Test BenchmarkResults class."""

    def test_initialization(self) -> None:
        """Test BenchmarkResults initialization with various data."""
        results = BenchmarkResultContainer.model_construct(features={}, metrics={})
        assert results.features == {}
        assert results.metrics == {}

    def test_algorithms_default_to_empty(self) -> None:
        """Test that the algorithms field defaults to an empty dict."""
        results = BenchmarkResultContainer(features={}, metrics={})
        assert results.algorithms == {}
        assert list(results.get_all_algorithms()) == []

    def test_get_all_algorithms(self) -> None:
        """Test get_all_algorithms across models and algorithms."""
        run1: Any = MagicMock()
        run2: Any = MagicMock()
        run3: Any = MagicMock()
        results = BenchmarkResultContainer.model_construct(
            features={},
            metrics={},
            algorithms={
                "model1": {"algo1": run1, "algo2": run2},
                "model2": {"algo1": run3},
            },
        )
        algorithm_list = list(results.get_all_algorithms())
        assert len(algorithm_list) == 3
        assert ("model1", "algo1", run1) in algorithm_list
        assert ("model1", "algo2", run2) in algorithm_list
        assert ("model2", "algo1", run3) in algorithm_list

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
        metric_results_container.__contains__.return_value = True
        metric_results_container.get_all.return_value = {"metric1": mr}
        metrics: dict[str, dict[str, Any]] = {"model1": {"algo1": metric_results_container}}
        results = BenchmarkResultContainer.model_construct(features={}, metrics=metrics)
        metric_list = list(results.get_all_metrics_of_type(metric_cls))
        assert len(metric_list) == 1
        assert metric_list[0] == ("model1", "algo1", mr)

        mr2: Any = MagicMock()
        mr3: Any = MagicMock()
        mr1_container: Any = MagicMock()
        mr1_container.__contains__.return_value = True
        mr1_container.get_all.return_value = {"metric1": mr}
        mr2_container: Any = MagicMock()
        mr2_container.__contains__.return_value = True
        mr2_container.get_all.return_value = {"metric2": mr2}
        mr3_container: Any = MagicMock()
        mr3_container.__contains__.return_value = True
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

    def test_get_all_metrics_of_type_skips_a_pair_without_that_metric(self) -> None:
        """Test a metric that failed for one algorithm does not break the plots of another.

        The pair simply contributes nothing: asking for a metric class the container does
        not hold is a programming error, but a missing result is a benchmark outcome.
        """
        without: Any = MagicMock()
        without.__contains__.return_value = False
        with_result: Any = MagicMock()
        with_result.__contains__.return_value = True
        with_result.get_all.return_value = {"metric1": MagicMock()}

        results = BenchmarkResultContainer.model_construct(
            features={}, metrics={"model1": {"failed": without, "solved": with_result}}
        )

        assert [algorithm for _, algorithm, _ in results.get_all_metrics_of_type(MagicMock())] == ["solved"]
        without.get_all.assert_not_called()

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
