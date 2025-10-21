from typing import ClassVar

from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.interfaces import IPlot
from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
from luna_bench._internal.user_models.metric_usermodel import MetricUserModel
from luna_bench.errors.run_errors.plots_errors.metrics_missing_error import MetricsMissingError
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class GenericMetricsPlot(IPlot):
    """
    Base class for plots that only require metrics.

    Provides metric preparation and validation functionality.
    Subclasses must implement the run method.

    Attributes
    ----------
    metrics_names : ClassVar[set[str]]
        Set of required metric names for this plot.
    metrics: dict[str, MetricUserModel] | None
        Dictionary with metrics. It should contain metrics after validation process.
        At the moment when run method will be called it should contain needed metrics.
    """

    metrics_names: ClassVar[set[str]] = set()
    metrics: dict[str, MetricUserModel] | None = None

    def _prepare_metrics(
        self,
        metrics: list[MetricUserModel],
    ) -> Result[dict[str, MetricUserModel], MetricsMissingError | UnknownLunaBenchError]:
        """
        Parse metrics from benchmark and compare with config.

        Parameters
        ----------
        metrics : list[MetricUserModel]
            List of benchmark's metrics.

        Returns
        -------
        Result[dict[str, IMetric], MetricsMissingError | UnknownLunaBenchError]
            Success with dictionary mapping metric names to metric instances,
            or Failure with MetricsMissingError if required metrics are missing.
        """
        result: dict[str, MetricUserModel] = {}
        for metric in metrics:
            if metric.name in self.metrics_names:
                result[metric.name] = metric

        metrics_diff = self.metrics_names - result.keys()
        if len(metrics_diff) > 0:
            return Failure(MetricsMissingError(list(metrics_diff)))

        return Success(result)

    def validate_plot(
        self,
        benchmark: BenchmarkUserModel,
    ) -> Result[None, PlotRunError | UnknownLunaBenchError]:
        """
        Validate that required metrics are present in the benchmark.

        Parameters
        ----------
        benchmark : BenchmarkUserModel
            The benchmark containing metrics and features.

        Returns
        -------
        Result[None, MetricsMissingError | FeaturesMissingError | UnknownLunaBenchError]
            Success if all required metrics are present, Failure with appropriate error otherwise.
        """
        metrics_result = self._prepare_metrics(benchmark.metrics)
        if not is_successful(metrics_result):
            return Failure(metrics_result.failure())
        self.metrics = metrics_result.unwrap()

        return Success(None)

    def add_metric(self, metric_name: str) -> None:
        """
        Add metric manually to a plot configuration.

        Parameters
        ----------
        metric_name : str
            Name of the metric to add.
        """
        self.metrics_names.add(metric_name)

    def has_metric(self, metric_name: str) -> bool:
        """
        Check if a metric is required by this plot.

        Parameters
        ----------
        metric_name : str
            Name of the metric to check.

        Returns
        -------
        bool
            True if the metric is in the required metrics set, False otherwise.
        """
        return metric_name in self.metrics_names
