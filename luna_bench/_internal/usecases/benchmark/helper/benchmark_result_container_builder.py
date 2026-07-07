"""Builder for a full benchmark result container."""

from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench.custom.result_containers.benchmark_result_container import (
    AlgorithmRunResult,
    BenchmarkResultContainer,
)
from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer
from luna_bench.custom.result_containers.metric_result_container import MetricResultContainer

if TYPE_CHECKING:
    from luna_bench.custom.types import (
        AlgorithmName,
        FeatureClass,
        FeatureComputed,
        FeatureName,
        MetricClass,
        MetricComputed,
        MetricName,
        ModelName,
    )
    from luna_bench.entities import BenchmarkEntity


class BenchmarkResultContainerBuilder:
    """Build a ``BenchmarkResultContainer`` with every result present on a benchmark.

    Unlike the per-plot builders (``FeatureResultBuilder``/``MetricResultBuilder``),
    which validate a list of *required* component classes, this builder collects
    everything that is available: all successful feature and metric results, and
    all algorithm run results (including failed runs, whose solution is ``None``).
    """

    def __init__(self, benchmark: BenchmarkEntity) -> None:
        """
        Initialize the builder with a benchmark.

        Parameters
        ----------
        benchmark : BenchmarkEntity
            The benchmark containing features, metrics, algorithms, and their results.
        """
        self.benchmark = benchmark

    def build(self) -> BenchmarkResultContainer:
        """
        Build the full result container from the benchmark.

        Returns
        -------
        BenchmarkResultContainer
            Container holding all feature, metric, and algorithm results of the benchmark.
        """
        features: dict[ModelName, dict[FeatureClass, dict[FeatureName, FeatureComputed]]] = {}
        for f in self.benchmark.features:
            for model_name, result_entity in f.results.items():
                if result_entity.result is not None:
                    features.setdefault(model_name, {}).setdefault(type(f.feature), {})[f.name] = (
                        result_entity.result,
                        f.feature,
                    )

        metrics: dict[ModelName, dict[AlgorithmName, dict[MetricClass, dict[MetricName, MetricComputed]]]] = {}
        for m in self.benchmark.metrics:
            for model_name, algo_results in m.results.items():
                for algorithm_name, metric_result_entity in algo_results.items():
                    if metric_result_entity.result is not None:
                        metrics.setdefault(model_name, {}).setdefault(algorithm_name, {}).setdefault(
                            type(m.metric), {}
                        )[m.name] = (metric_result_entity.result, m.metric)

        algorithms: dict[ModelName, dict[AlgorithmName, AlgorithmRunResult]] = {}
        for a in self.benchmark.algorithms:
            for model_name, algo_result_entity in a.results.items():
                algorithms.setdefault(model_name, {})[a.name] = AlgorithmRunResult(
                    solution=algo_result_entity.solution,
                    meta_data=algo_result_entity.meta_data.model_dump() if algo_result_entity.meta_data else None,
                    algorithm=a.algorithm,
                )

        return BenchmarkResultContainer(
            features={
                model_name: FeatureResultContainer.model_construct(data=data) for model_name, data in features.items()
            },
            metrics={
                model_name: {
                    algorithm_name: MetricResultContainer.model_construct(data=data)
                    for algorithm_name, data in algo_data.items()
                }
                for model_name, algo_data in metrics.items()
            },
            algorithms=algorithms,
        )
