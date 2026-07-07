from __future__ import annotations

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.usecases.benchmark.helper.benchmark_result_container_builder import (
    BenchmarkResultContainerBuilder,
)
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


class TestBenchmarkResultContainerBuilder:
    def test_empty_benchmark(self) -> None:
        container = BenchmarkResultContainerBuilder(_make_benchmark()).build()

        assert container.features == {}
        assert container.metrics == {}
        assert container.algorithms == {}

    def test_features_grouped_by_model_and_name(self) -> None:
        feature = make_feature_entity("feat_a", ("model_1", {"count": 42}), ("model_2", {"count": 7}))
        container = BenchmarkResultContainerBuilder(_make_benchmark(features=[feature])).build()

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
        container = BenchmarkResultContainerBuilder(_make_benchmark(features=[feature])).build()

        assert set(container.features) == {"model_1"}

    def test_metrics_grouped_by_model_algorithm_and_name(self) -> None:
        metric = make_metric_entity(
            "accuracy",
            ("algo_1", "model_1", {"score": 0.9}),
            ("algo_2", "model_1", {"score": 0.8}),
        )
        container = BenchmarkResultContainerBuilder(_make_benchmark(metrics=[metric])).build()

        assert set(container.metrics["model_1"]) == {"algo_1", "algo_2"}
        result = container.metrics["model_1"]["algo_1"].get(MockMetric, "accuracy")
        assert result.model_dump() == {"score": 0.9}

    def test_metric_without_result_is_skipped(self) -> None:
        metric = make_metric_entity("accuracy", ("algo_1", "model_1", {}), status=JobStatus.FAILED, error="boom")
        container = BenchmarkResultContainerBuilder(_make_benchmark(metrics=[metric])).build()

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
        container = BenchmarkResultContainerBuilder(_make_benchmark(algorithms=[algo])).build()

        run_result = container.algorithms["model_1"]["algo_1"]
        assert run_result.solution is None
        assert run_result.meta_data == {"runtime": 1.5}
        assert run_result.algorithm is algo.algorithm

    def test_multiple_algorithms_and_models(self) -> None:
        algo1 = make_algo_entity("algo_1", ["model_1", "model_2"])
        algo2 = make_algo_entity("algo_2", ["model_1"])
        container = BenchmarkResultContainerBuilder(_make_benchmark(algorithms=[algo1, algo2])).build()

        assert set(container.algorithms) == {"model_1", "model_2"}
        assert set(container.algorithms["model_1"]) == {"algo_1", "algo_2"}
        assert set(container.algorithms["model_2"]) == {"algo_1"}
        assert list(container.get_all_algorithms()) == [
            ("model_1", "algo_1", container.algorithms["model_1"]["algo_1"]),
            ("model_1", "algo_2", container.algorithms["model_1"]["algo_2"]),
            ("model_2", "algo_1", container.algorithms["model_2"]["algo_1"]),
        ]
