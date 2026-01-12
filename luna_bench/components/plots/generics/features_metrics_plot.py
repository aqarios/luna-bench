from abc import abstractmethod

from pydantic import BaseModel
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.interfaces.plot_i import IPlot
from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
from luna_bench._internal.user_models.feature_usermodel import FeatureUserModel
from luna_bench._internal.user_models.metric_usermodel import MetricUserModel
from luna_bench.components.plots.generics.mixins.features_plot_mixin import FeaturesPlotMixin
from luna_bench.components.plots.generics.mixins.metrics_plot_mixin import MetricsPlotMixin
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class FeaturesAndMetricsValidationResult(BaseModel):
    """
    Container for validated metrics and features data passed to plot run methods.

    Attributes
    ----------
    metrics : dict[str, MetricUserModel]
        Dictionary mapping metric names to metric instances. Contains only
        the metrics required by the plot.
    features : dict[str, FeatureUserModel]
        Dictionary mapping feature names to feature instances. Contains only
        the features required by the plot.
    """

    metrics: dict[str, MetricUserModel]
    features: dict[str, FeatureUserModel]


class GenericFeaturesMetricsPlot(
    FeaturesPlotMixin,
    MetricsPlotMixin,
    IPlot[FeaturesAndMetricsValidationResult],
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

    @abstractmethod
    def run(self, data: FeaturesAndMetricsValidationResult) -> None:
        """
        Generate the plot using the provided metrics and features.

        This method must be implemented by subclasses to define the specific
        plotting logic for visualizations that combine both metrics and features.

        Parameters
        ----------
        data : FeaturesAndMetricsValidationResult
            Validated metrics and features container. Access metrics via data.metrics
            (contains only metrics specified in metrics_names) and features via
            data.features (contains only features specified in features_names).

        Returns
        -------
        None
            The method should generate and save/display the plot as a side effect.
        """

    def validate_plot(
        self,
        benchmark: BenchmarkUserModel,
    ) -> Result[FeaturesAndMetricsValidationResult, PlotRunError | UnknownLunaBenchError]:
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

        return Success(
            FeaturesAndMetricsValidationResult(
                features=features_result.unwrap(),
                metrics=metrics_result.unwrap(),
            )
        )
