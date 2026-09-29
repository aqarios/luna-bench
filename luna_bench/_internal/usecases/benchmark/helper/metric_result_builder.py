"""Builder for metric result structures and lookup tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from luna_bench.custom import BaseMetric  # noqa: TC001
from luna_bench.custom.result_containers.metric_result_container import MetricResultContainer
from luna_bench.custom.types import (  # noqa: TC001
    AlgorithmName,
    MetricClass,
    MetricComputed,
    MetricName,
    ModelName,
)
from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError

if TYPE_CHECKING:
    from luna_bench.custom.base_results.metric_result import MetricResult
    from luna_bench.entities import BenchmarkEntity


class MetricResultBuilder:
    """Builder for metric result structures from a benchmark."""

    def __init__(self, benchmark: BenchmarkEntity) -> None:
        """
        Initialize the builder with a benchmark.

        Parameters
        ----------
        benchmark : BenchmarkEntity
            The benchmark containing metrics and their results.
        """
        self.benchmark = benchmark
        self._lookup_map = self._build_lookup_map()

    def _build_lookup_map(
        self,
    ) -> dict[
        tuple[type[BaseMetric], AlgorithmName, ModelName],
        dict[int, tuple[MetricResult, BaseMetric, MetricName]],
    ]:
        """
        Build a lookup table of metric results by (type, algorithm, model) for efficient access.

        An algorithm run more than once has one result per repetition, so the innermost
        mapping is keyed by it.

        Returns
        -------
        dict[tuple[type[BaseMetric], AlgorithmName, ModelName], dict[int, tuple[...]]]
            Dict indexed by (metric_class, algorithm_name, model_name), then by repetition.
        """
        metric_map: dict[
            tuple[type[BaseMetric], AlgorithmName, ModelName],
            dict[int, tuple[MetricResult, BaseMetric, MetricName]],
        ] = {}
        for m in self.benchmark.metrics:
            metric_type: type[BaseMetric] = type(m.metric)
            metric_config: BaseMetric = m.metric
            for model_name, algo_results in m.results.items():
                for algo_name, per_repetition in algo_results.items():
                    for result in per_repetition:
                        r: MetricResult | None = result.result
                        if r is not None:
                            metric_map.setdefault((metric_type, algo_name, model_name), {})[result.repetition] = (
                                r,
                                metric_config,
                                m.name,
                            )

        return metric_map

    def results(
        self,
        model_name: ModelName,
        algorithm_name: AlgorithmName,
        required_metrics: list[MetricClass],
    ) -> Result[list[MetricResultContainer], RunMetricMissingError]:
        """
        Build and validate metric results for one algorithm and model, per repetition.

        A repetition counts only if every required metric was computed on it - a run
        missing one of them is left out rather than handed on half-filled - and the
        algorithm counts only if at least one of its runs did.

        Parameters
        ----------
        model_name : ModelName
            The model name to retrieve metric results for.
        algorithm_name : AlgorithmName
            The algorithm whose runs to retrieve them for.
        required_metrics : list[MetricClass]
            The metric classes that have to be present.

        Returns
        -------
        Result[list[MetricResultContainer], RunMetricMissingError]
            Success with one container per repetition, ordered by it, or Failure if a
            required metric is missing for every run.
        """
        per_repetition: dict[int, dict[MetricClass, dict[MetricName, MetricComputed]]] = {}

        for metric_cls in required_metrics:
            key = (metric_cls, algorithm_name, model_name)
            if key not in self._lookup_map:
                return Failure(RunMetricMissingError(metric_cls.__name__, self.benchmark.name))

            for repetition, data in self._lookup_map[key].items():
                # Keys here are from the _build_lookup_map function
                # '(metric_type, algo_name, model_name)' -> repetition -> (result, config, name)
                per_repetition.setdefault(repetition, {}).setdefault(metric_cls, {})[data[2]] = (data[0], data[1])

        complete = {
            repetition: data
            for repetition, data in sorted(per_repetition.items())
            if all(metric_cls in data for metric_cls in required_metrics)
        }
        if required_metrics and not complete:
            return Failure(RunMetricMissingError(required_metrics[0].__name__, self.benchmark.name))

        return Success(
            [
                MetricResultContainer.model_construct(data=data, repetition=repetition)
                for repetition, data in complete.items()
            ]
        )
