"""Builder for metric result structures and lookup tables."""

from __future__ import annotations

from typing import TYPE_CHECKING

from returns.result import Failure, Result, Success

from luna_bench.base_components import BaseMetric  # noqa: TC001
from luna_bench.base_components.data_types.metric_results import MetricResults
from luna_bench.errors.run_errors.run_metric_missing_error import RunMetricMissingError
from luna_bench.types import (  # noqa: TC001
    AlgorithmName,
    MetricClass,
    MetricComputed,
    MetricName,
    MetricResult,
    ModelName,
)

if TYPE_CHECKING:
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
    ) -> dict[tuple[type[BaseMetric], AlgorithmName, ModelName], tuple[MetricResult, BaseMetric, MetricName]]:
        """
        Build a lookup table of metric results by (type, algorithm, model) for efficient access.

        Returns
        -------
        dict[tuple[type[BaseMetric], AlgorithmName, ModelName], tuple[MetricResult, BaseMetric]]
            Dict indexed by (metric_class, algorithm_name, model_name) containing metric results.
        """
        metric_map: dict[
            tuple[type[BaseMetric], AlgorithmName, ModelName], tuple[MetricResult, BaseMetric, MetricName]
        ] = {}
        for m in self.benchmark.metrics:
            metric_type: type[BaseMetric] = type(m.metric)
            metric_config: BaseMetric = m.metric
            for model_name, algo_results in m.results.items():
                for algo_name, result in algo_results.items():
                    r: MetricResult | None = result.result
                    if r is not None:
                        metric_map[(metric_type, algo_name, model_name)] = (r, metric_config, m.name)

        return metric_map

    def results(
        self,
        model_name: ModelName,
        algorithm_name: AlgorithmName,
        required_metrics: list[MetricClass],
    ) -> Result[MetricResults, RunMetricMissingError]:
        """
        Build and validate feature results for a metric and model.

        Parameters
        ----------
        model_name : ModelName
            The model name to retrieve features for.
        metric : MetricEntity
            The metric requiring specific features.

        Returns
        -------
        Result[FeatureResults, RunFeatureMissingError]
            Success with FeatureResults if all required features are available,
            Failure with RunFeatureMissingError if any required feature is missing.
        """
        metric_data: dict[MetricClass, dict[MetricName, MetricComputed]] = {m: {} for m in required_metrics}

        for metric_cls, m_dict in metric_data.items():
            key = (metric_cls, algorithm_name, model_name)
            if key not in self._lookup_map:
                return Failure(RunMetricMissingError(metric_cls.__name__, self.benchmark.name))
            data = self._lookup_map[key]
            m_dict[data[2]] = (data[0], data[1])  # TODO make this a bit cleaner

        return Success(
            MetricResults.model_construct(
                data=metric_data,
                allowed=required_metrics,
            )
        )
