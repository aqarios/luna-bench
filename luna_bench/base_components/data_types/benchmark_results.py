from __future__ import annotations

from collections.abc import Generator

from pydantic import BaseModel

from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.base_components.data_types.metric_results import MetricResults
from luna_bench.types import AlgorithmName, MetricClass, ModelName


class BenchmarkResults(BaseModel):
    """Benchmark results container."""

    features: dict[ModelName, FeatureResults]
    metrics: dict[ModelName, dict[AlgorithmName, MetricResults]]

    def get_all_metrics(self) -> Generator[tuple[ModelName, AlgorithmName, MetricResults]]:
        for model_name, metrics in self.metrics.items():
            for algorithm_name, metric_results in metrics.items():
                yield model_name, algorithm_name, metric_results

    def get_all_metrics_of_type(
        self, metric_cls: MetricClass
    ) -> Generator[tuple[ModelName, AlgorithmName, MetricResults]]:
        for model_name, algorithm_name, metric_results in self.get_all_metrics():
            for metric_result in metric_results.get_all(metric_cls).values():
                if metric_result is not None:
                    yield model_name, algorithm_name, metric_result
