from __future__ import annotations

from typing import ClassVar, cast

import pytest
from returns.pipeline import is_successful

from luna_bench._internal.usecases.benchmark.helper.metric_result_builder import MetricResultBuilder
from luna_bench.base_components import BaseMetric
from luna_bench.entities import BenchmarkEntity, MetricEntity
from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError
from luna_bench.types import MetricResult
from tests.unit.fixtures.mock_components import MockMetric
from tests.unit.fixtures.mock_entities import make_metric_entity


class TestMetricResultBuilder:
    class MockMetric2(BaseMetric[MetricResult]):
        registered_id: ClassVar[str] = "mock_metric_2"

        def run(self, _solution: object, _feature_results: object) -> MetricResult:
            return MetricResult()

    @staticmethod
    def _make_benchmark(metrics: list[MetricEntity]) -> BenchmarkEntity:
        return BenchmarkEntity(
            name="test_bench",
            modelset=None,
            features=[],
            algorithms=[],
            metrics=metrics,
            plots=[],
        )

    @pytest.mark.parametrize(
        "metrics",
        [
            [],
            [make_metric_entity("metric_a", ("algo_1", "model_1", {"value": 1}))],
            [make_metric_entity("metric_a", ("algo_1", "model_1", {"value": 1}), ("algo_1", "model_2", {"value": 2}))],
            [
                make_metric_entity("metric_a", ("algo_1", "model_1", {"value": 1})),
                make_metric_entity("metric_b", ("algo_1", "model_1", {"value": 2})),
            ],
            [
                make_metric_entity(
                    "metric_a", ("algo_1", "model_1", {"value": 1}), ("algo_1", "model_2", {"value": 2})
                ),
                make_metric_entity(
                    "metric_b", ("algo_1", "model_1", {"value": 3}), ("algo_1", "model_2", {"value": 4})
                ),
            ],
        ],
    )
    def test_init_builds_lookup_map(self, metrics: list[MetricEntity]) -> None:
        benchmark = self._make_benchmark(metrics)
        builder = MetricResultBuilder(benchmark)

        assert builder.benchmark is benchmark
        assert isinstance(builder._lookup_map, dict)

    def test_results_success(self) -> None:
        metric = make_metric_entity("metric_a", ("algo_1", "model_1", {"value": 1}))
        builder = MetricResultBuilder(self._make_benchmark([metric]))
        result = builder.results("model_1", "algo_1", [MockMetric])

        assert is_successful(result)

    def test_results_missing_model(self) -> None:
        metric = make_metric_entity("metric_a", ("algo_1", "model_1", {"value": 1}))
        builder = MetricResultBuilder(self._make_benchmark([metric]))
        result = builder.results("missing", "algo_1", [MockMetric])

        assert not is_successful(result)
        assert isinstance(result.failure(), RunMetricMissingError)

    def test_results_missing_algorithm(self) -> None:
        metric = make_metric_entity("metric_a", ("algo_1", "model_1", {"value": 1}))
        builder = MetricResultBuilder(self._make_benchmark([metric]))
        result = builder.results("model_1", "missing_algo", [MockMetric])

        assert not is_successful(result)
        assert isinstance(result.failure(), RunMetricMissingError)

    def test_results_missing_metric_class(self) -> None:
        metric = make_metric_entity("metric_a", ("algo_1", "model_1", {"value": 1}))
        builder = MetricResultBuilder(self._make_benchmark([metric]))
        result = builder.results("model_1", "algo_1", [self.MockMetric2])

        assert not is_successful(result)
        assert isinstance(result.failure(), RunMetricMissingError)

    def test_results_empty_benchmark(self) -> None:
        builder = MetricResultBuilder(self._make_benchmark([]))
        result = builder.results("model_1", "algo_1", [MockMetric])

        assert not is_successful(result)

    @pytest.mark.parametrize(
        ("num_metrics", "num_models", "num_algos"), [(1, 1, 1), (3, 1, 1), (1, 5, 1), (1, 1, 3), (5, 5, 3)]
    )
    def test_lookup_map_size(self, num_metrics: int, num_models: int, num_algos: int) -> None:
        metrics = [
            make_metric_entity(
                f"metric_{i}",
                *[
                    (f"algo_{a}", f"model_{m}", cast("dict[str, object]", {"value": i * 100 + a * 10 + m}))
                    for a in range(num_algos)
                    for m in range(num_models)
                ],
            )
            for i in range(num_metrics)
        ]
        builder = MetricResultBuilder(self._make_benchmark(metrics))

        expected = num_models * num_algos if (num_metrics > 0 and num_models > 0 and num_algos > 0) else 0
        assert len(builder._lookup_map) == expected
        for inner in builder._lookup_map.values():
            assert len(inner) == 3

    def test_results_multiple_calls_independent(self) -> None:
        metric = make_metric_entity("metric_a", ("algo_1", "model_1", {"value": 1}))
        builder = MetricResultBuilder(self._make_benchmark([metric]))

        r1 = builder.results("model_1", "algo_1", [MockMetric]).unwrap()
        r2 = builder.results("model_1", "algo_1", [MockMetric]).unwrap()

        assert r1 is not r2

    @pytest.mark.parametrize(
        ("models", "algorithms", "query_model", "query_algo", "should_succeed"),
        [
            (["model_1"], ["algo_1"], "model_1", "algo_1", True),
            (["model_1"], ["algo_1"], "model_2", "algo_1", False),
            (["model_1"], ["algo_1"], "model_1", "algo_2", False),
            (["model_1", "model_2"], ["algo_1"], "model_1", "algo_1", True),
            (["model_1", "model_2"], ["algo_1"], "model_2", "algo_1", True),
            (["model_1", "model_2"], ["algo_1"], "model_3", "algo_1", False),
            (["model_1"], ["algo_1", "algo_2"], "model_1", "algo_1", True),
            (["model_1"], ["algo_1", "algo_2"], "model_1", "algo_2", True),
            (["model_1"], ["algo_1", "algo_2"], "model_1", "algo_3", False),
        ],
    )
    def test_results_availability(
        self,
        *,
        models: list[str],
        algorithms: list[str],
        query_model: str,
        query_algo: str,
        should_succeed: bool,
    ) -> None:
        metric = make_metric_entity(
            "metric_a",
            *[
                (algo, model, cast("dict[str, object]", {"value": hash((algo, model))}))
                for algo in algorithms
                for model in models
            ],
        )
        builder = MetricResultBuilder(self._make_benchmark([metric]))
        result = builder.results(query_model, query_algo, [MockMetric])

        assert is_successful(result) == should_succeed
