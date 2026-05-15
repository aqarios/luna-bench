from __future__ import annotations

from collections.abc import Generator

from pydantic import BaseModel

from luna_bench.custom.base_results.metric_result import MetricResult
from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer
from luna_bench.custom.result_containers.metric_result_container import MetricResultContainer
from luna_bench.custom.types import AlgorithmName, MetricClass, ModelName


class BenchmarkResultContainer(BaseModel):
    """Container for benchmark outputs grouped by model and algorithm."""

    features: dict[ModelName, FeatureResultContainer]
    metrics: dict[ModelName, dict[AlgorithmName, MetricResultContainer]]

    def get_all_metrics(self) -> Generator[tuple[ModelName, AlgorithmName, MetricResultContainer]]:
        """Yield all metric result groups across models and algorithms.

        Yields
        ------
        tuple[ModelName, AlgorithmName, MetricResults]
            A tuple containing the model name, algorithm name, and
            corresponding metric results.
        """
        for model_name, metrics in self.metrics.items():
            for algorithm_name, metric_results in metrics.items():
                yield model_name, algorithm_name, metric_results

    def get_all_metrics_of_type[TMetricResult: MetricResult](
        self, metric_cls: MetricClass[TMetricResult]
    ) -> Generator[tuple[ModelName, AlgorithmName, TMetricResult]]:
        """Yield all metric results matching a specific metric class.

        Parameters
        ----------
        metric_cls : MetricClass
            The metric class used to filter metric results.

        Yields
        ------
        tuple[ModelName, AlgorithmName, MetricResult]
            A tuple containing the model name, algorithm name, and each
            non-null metric result of the requested type.
        """
        for model_name, algorithm_name, metric_results in self.get_all_metrics():
            for metric_result in metric_results.get_all(metric_cls).values():
                if metric_result is not None:
                    yield model_name, algorithm_name, metric_result
