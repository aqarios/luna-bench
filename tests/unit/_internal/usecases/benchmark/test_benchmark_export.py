from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench._internal.usecases.benchmark.benchmark_export import BenchmarkExportUcImpl
from luna_bench.entities import BenchmarkEntity
from tests.unit.fixtures.mock_entities import make_algo_entity, make_feature_entity, make_metric_entity

if TYPE_CHECKING:
    from luna_bench.custom import BenchmarkResultContainer


class TestBenchmarkExportUc:
    def test_builds_container_and_delegates_to_exporter(self) -> None:
        benchmark = BenchmarkEntity(
            name="test_bench",
            modelset=None,
            features=[make_feature_entity("num_vars", ("model1", {"count": 42}))],
            algorithms=[make_algo_entity("algo1", ["model1"])],
            metrics=[make_metric_entity("accuracy", ("algo1", "model1", {"score": 0.95}))],
            plots=[],
        )
        captured: list[BenchmarkResultContainer] = []

        class CapturingExporter:
            def export(self, benchmark_results: BenchmarkResultContainer) -> str:
                captured.append(benchmark_results)
                return "payload"

        result = BenchmarkExportUcImpl()(benchmark, CapturingExporter())

        assert result == "payload"
        container = captured[0]
        assert set(container.features) == {"model1"}
        assert set(container.metrics["model1"]) == {"algo1"}
        assert set(container.algorithms["model1"]) == {"algo1"}
