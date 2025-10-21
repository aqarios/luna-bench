from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
from luna_bench.components.plots.generics.features_plot import GenericFeaturesPlot
from luna_bench.components.plots.generics.metrics_plot import GenericMetricsPlot
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class GenericFeaturesMetricsPlot(
    GenericMetricsPlot,
    GenericFeaturesPlot,
):
    """
    Base class for plots that require both metrics and features.

    Provides preparation and validation for both metrics and features.
    Subclasses must implement the run method.

    Attributes
    ----------
    metrics_names : ClassVar[set[str]]
        Set of required metric names for this plot.
    features_names : ClassVar[set[str]]
        Set of required feature names for this plot.
    metrics: dict[str, MetricUserModel] | None
        Dictionary with metrics. It should contain metrics after validation process.
        At the moment when run method will be called it should contain needed metrics.
    features: dict[str, FeatureUserModel] | None
        Dictionary with features. It should contain features after validation process.
        At the moment when run method will be called it should contain needed featres.
    """

    def validate_plot(
        self,
        benchmark: BenchmarkUserModel,
    ) -> Result[None, PlotRunError | UnknownLunaBenchError]:
        """
        Validate that required metrics and features are present in the benchmark.

        Parameters
        ----------
        benchmark : BenchmarkUserModel
            The benchmark containing metrics and features.

        Returns
        -------
        Result[None, MetricsMissingError | FeaturesMissingError | UnknownLunaBenchError]
            Success if all required metrics and features are present, Failure with appropriate error otherwise.
        """
        metrics_result = self._prepare_metrics(benchmark.metrics)
        if not is_successful(metrics_result):
            return Failure(metrics_result.failure())

        features_result = self._prepare_features(benchmark.features)
        if not is_successful(features_result):
            return Failure(features_result.failure())

        return Success(None)
