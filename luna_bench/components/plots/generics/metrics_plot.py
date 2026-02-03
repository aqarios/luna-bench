from abc import abstractmethod

from pydantic import BaseModel
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench.base_components import BasePlot
from luna_bench.components.plots.generics.mixins.metrics_plot_mixin import MetricsPlotMixin
from luna_bench.entities.benchmark_entity import BenchmarkEntity
from luna_bench.entities.metric_entity import MetricEntity
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class MetricsValidationResult(BaseModel):
    """
    Container for validated metrics data passed to plot run methods.

    Attributes
    ----------
    metrics : dict[str, MetricEntity]
        Dictionary mapping metric names to metric instances. Contains only
        the metrics required by the plot.
    """

    metrics: dict[str, MetricEntity]


class GenericMetricsPlot(BasePlot[MetricsValidationResult], MetricsPlotMixin):
    """
    Base class for plots that only require metrics.

    Provides metric preparation and validation functionality.
    Subclasses must implement the run method.

    Attributes
    ----------
    metrics_names : ClassVar[set[str]]
        Set of required metric names for this plot.
    """

    @abstractmethod
    def run(self, data: MetricsValidationResult) -> None:
        """
        Generate the plot using the provided metrics.

        This method must be implemented by subclasses to define the specific
        plotting logic for metrics-based visualizations.

        Parameters
        ----------
        data : MetricsValidationResult
            Validated metrics container. Access metrics via data.metrics,
            which contains only the metrics specified in the class's
            metrics_names attribute.

        Returns
        -------
        None
            The method should generate and save/display the plot as a side effect.
        """

    def validate_plot(
        self,
        benchmark: BenchmarkEntity,
    ) -> Result[MetricsValidationResult, PlotRunError | UnknownLunaBenchError]:
        """
        Validate that required metrics are present in the benchmark.

        Parameters
        ----------
        benchmark : BenchmarkEntity
            The benchmark containing metrics and features.

        Returns
        -------
        Result[None, MetricsMissingError | FeaturesMissingError | UnknownLunaBenchError]
            Success if all required metrics are present, Failure with appropriate error otherwise.
        """
        metrics_result = self._prepare_metrics(benchmark.metrics)
        if not is_successful(metrics_result):
            return Failure(metrics_result.failure())

        return Success(MetricsValidationResult(metrics=metrics_result.unwrap()))
