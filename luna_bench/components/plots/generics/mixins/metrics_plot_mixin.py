"""Mixin providing metrics validation and management for plot components."""

from typing import ClassVar

from returns.result import Failure, Result, Success

from luna_bench._internal.user_models.metric_usermodel import MetricUserModel
from luna_bench.errors.run_errors.plots_errors.metrics_missing_error import MetricsMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class MetricsPlotMixin:
    """
    Mixin that adds metrics validation and management capabilities to plot classes.

    This mixin provides functionality to validate that required metrics are present
    in a benchmark configuration and to manage the set of metrics needed by a plot.

    Attributes
    ----------
    metrics_names : set[str]
        Class-level set of metric names required by the plot.

    Methods
    -------
    _prepare_metrics(metrics)
        Validate and map benchmark metrics against required metrics.
    add_metric(metric_name)
        Manually add a metric to the required metrics set.
    has_metric(metric_name)
        Check if a metric is in the required metrics set.
    """

    metrics_names: ClassVar[set[str]] = set()

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
