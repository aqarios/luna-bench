from __future__ import annotations

from collections.abc import Generator
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from luna_bench.custom.base_results.metric_result import MetricResult
from luna_bench.custom.result_containers.algorithm_result_container import AlgorithmResultContainer
from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer
from luna_bench.custom.result_containers.metric_result_container import MetricResultContainer
from luna_bench.custom.types import AlgorithmName, MetricClass, ModelName

if TYPE_CHECKING:
    from luna_bench.custom.types import (
        FeatureClass,
        FeatureComputed,
        FeatureName,
        MetricComputed,
        MetricName,
    )
    from luna_bench.entities import BenchmarkEntity


class BenchmarkResultContainer(BaseModel):
    """Container for benchmark outputs grouped by model and algorithm."""

    features: dict[ModelName, FeatureResultContainer]
    #: One entry per repetition of the algorithm, ordered by it.
    metrics: dict[ModelName, dict[AlgorithmName, list[MetricResultContainer]]]
    #: One entry per repetition of the algorithm, ordered by it.
    algorithms: dict[ModelName, dict[AlgorithmName, list[AlgorithmResultContainer]]] = Field(default_factory=dict)

    @classmethod
    def from_benchmark(cls, benchmark: BenchmarkEntity) -> BenchmarkResultContainer:
        """Build a container with every result present on a benchmark.

        Unlike the per-plot builders (``FeatureResultBuilder``/``MetricResultBuilder``),
        which validate a list of *required* component classes, this collects
        everything that is available: all successful feature and metric results,
        and all algorithm run results (including failed runs, whose solution is
        ``None``).

        Parameters
        ----------
        benchmark : BenchmarkEntity
            The benchmark containing features, metrics, algorithms, and their results.

        Returns
        -------
        BenchmarkResultContainer
            Container holding all feature, metric, and algorithm results of the benchmark.
        """
        features: dict[ModelName, dict[FeatureClass, dict[FeatureName, FeatureComputed]]] = {}
        for f in benchmark.features:
            for model_name, result_entity in f.results.items():
                if result_entity.result is not None:
                    features.setdefault(model_name, {}).setdefault(type(f.feature), {})[f.name] = (
                        result_entity.result,
                        f.feature,
                    )

        # Keyed by repetition while collecting, because the metrics of one run are spread
        # over the benchmark's metric entities and only complete once all of them are seen.
        metrics: dict[
            ModelName, dict[AlgorithmName, dict[int, dict[MetricClass, dict[MetricName, MetricComputed]]]]
        ] = {}
        for m in benchmark.metrics:
            for model_name, algo_results in m.results.items():
                for algorithm_name, per_repetition in algo_results.items():
                    for metric_result_entity in per_repetition:
                        if metric_result_entity.result is not None:
                            metrics.setdefault(model_name, {}).setdefault(algorithm_name, {}).setdefault(
                                metric_result_entity.repetition, {}
                            ).setdefault(type(m.metric), {})[m.name] = (metric_result_entity.result, m.metric)

        return cls(
            features={
                model_name: FeatureResultContainer.model_construct(data=data) for model_name, data in features.items()
            },
            metrics={
                model_name: {
                    algorithm_name: [
                        MetricResultContainer.model_construct(data=data, repetition=repetition)
                        for repetition, data in sorted(per_repetition.items())
                    ]
                    for algorithm_name, per_repetition in algo_data.items()
                }
                for model_name, algo_data in metrics.items()
            },
            algorithms=cls.algorithm_results(benchmark),
        )

    @staticmethod
    def algorithm_results(
        benchmark: BenchmarkEntity,
    ) -> dict[ModelName, dict[AlgorithmName, list[AlgorithmResultContainer]]]:
        """Return every algorithm run of a benchmark, together with its configuration.

        Split out of `from_benchmark` because a consumer may want the runs without
        paying for the feature and metric results - the plot runner, which builds those
        two from the *required* components of a plot, but still wants to know what each
        algorithm was configured with.

        Parameters
        ----------
        benchmark : BenchmarkEntity
            The benchmark containing algorithms and their results.

        Returns
        -------
        dict[ModelName, dict[AlgorithmName, list[AlgorithmResultContainer]]]
            Run results per model and algorithm, one per repetition and ordered by it,
            including failed runs, whose solution is ``None``.
        """
        algorithms: dict[ModelName, dict[AlgorithmName, list[AlgorithmResultContainer]]] = {}
        for a in benchmark.algorithms:
            for model_name, runs in a.results.items():
                algorithms.setdefault(model_name, {})[a.name] = [
                    AlgorithmResultContainer(
                        solution=run.solution,
                        metadata=run.metadata,
                        algorithm=a.algorithm,
                        repetition=run.repetition,
                    )
                    for run in runs
                ]
        return algorithms

    def get_all_algorithms(self) -> Generator[tuple[ModelName, AlgorithmName, AlgorithmResultContainer]]:
        """Yield all algorithm run results across models and algorithms.

        An algorithm added with ``repetitions`` is yielded once per repetition, so a
        consumer that aggregates - a plot, a table - sees every run rather than one of
        them. Which run a result belongs to is on the container.

        Yields
        ------
        tuple[ModelName, AlgorithmName, AlgorithmResultContainer]
            A tuple containing the model name, algorithm name, and
            corresponding algorithm result container.
        """
        for model_name, algorithms in self.algorithms.items():
            for algorithm_name, runs in algorithms.items():
                for run_result in runs:
                    yield model_name, algorithm_name, run_result

    def get_all_metrics(self) -> Generator[tuple[ModelName, AlgorithmName, MetricResultContainer]]:
        """Yield all metric result groups across models and algorithms.

        An algorithm added with ``repetitions`` is yielded once per repetition, since
        every run is evaluated on its own. Which run a group belongs to is on the
        container.

        Yields
        ------
        tuple[ModelName, AlgorithmName, MetricResults]
            A tuple containing the model name, algorithm name, and
            corresponding metric results.
        """
        for model_name, metrics in self.metrics.items():
            for algorithm_name, per_repetition in metrics.items():
                for metric_results in per_repetition:
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
            # A metric that failed for one model and algorithm leaves that pair without a
            # result of this class. It contributes nothing, which is not the same as the
            # caller asking for a metric the benchmark never computed.
            if metric_cls not in metric_results:
                continue
            for metric_result in metric_results.get_all(metric_cls).values():
                if metric_result is not None:
                    yield model_name, algorithm_name, metric_result
