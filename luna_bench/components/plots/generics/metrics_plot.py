from abc import abstractmethod

from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.interfaces import IPlot
from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
from luna_bench._internal.user_models.metric_usermodel import MetricUserModel
from luna_bench.components.plots.generics.mixins.metrics_plot_mixin import MetricsPlotMixin
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class GenericMetricsPlot(IPlot, MetricsPlotMixin):
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
    def run(self, metrics: dict[str, MetricUserModel]) -> None:
        """
        Generate the plot using the provided metrics.

        This method must be implemented by subclasses to define the specific
        plotting logic for metrics-based visualizations.

        Parameters
        ----------
        metrics : dict[str, MetricUserModel]
            Dictionary mapping metric names to metric instances. Contains only
            the metrics specified in the class's metrics_names attribute.

        Returns
        -------
        None
            The method should generate and save/display the plot as a side effect.
        """

    def validate_plot(
        self,
        benchmark: BenchmarkUserModel,
    ) -> Result[dict[str, dict[str, MetricUserModel]], PlotRunError | UnknownLunaBenchError]:
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

        return Success({"metrics": metrics_result.unwrap()})
