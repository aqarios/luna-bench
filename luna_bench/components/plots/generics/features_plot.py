from abc import abstractmethod

from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.interfaces.plot_i import IPlot
from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
from luna_bench._internal.user_models.feature_usermodel import FeatureUserModel
from luna_bench.components.plots.generics.mixins.features_plot_mixin import FeaturesPlotMixin
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class GenericFeaturesPlot(IPlot, FeaturesPlotMixin):
    """
    Base class for plots that only require features.

    Provides feature preparation and validation functionality.
    Subclasses must implement the run method.

    Attributes
    ----------
    features_names : ClassVar[set[str]]
        Set of required feature names for this plot.
    features: dict[str, FeatureUserModel] | None
        Dictionary with features. It should contain features after validation process.
        At the moment when run method will be called it should contain needed featres.

    """

    @abstractmethod
    def run(self, features: dict[str, FeatureUserModel]) -> None:
        """
        Generate the plot using the provided features.

        This method must be implemented by subclasses to define the specific
        plotting logic for feature-based visualizations.

        Parameters
        ----------
        features : dict[str, FeatureUserModel]
            Dictionary mapping feature names to feature instances. Contains only
            the features specified in the class's features_names attribute.

        Returns
        -------
        None
            The method should generate and save/display the plot as a side effect.
        """

    def validate_plot(
        self,
        benchmark: BenchmarkUserModel,
    ) -> Result[dict[str, dict[str, FeatureUserModel]], PlotRunError | UnknownLunaBenchError]:
        """
        Validate that required features are present in the benchmark.

        Parameters
        ----------
        benchmark: BenchmarkUserModel
            The benchmark containing features.

        Returns
        -------
        Result[None, MetricsMissingError | FeaturesMissingError | UnknownLunaBenchError]
            Success if all required features are present, Failure with appropriate error otherwise.
        """
        features = self._prepare_features(
            benchmark.features,
        )
        if not is_successful(features):
            return Failure(features.failure())

        return Success({"features": features.unwrap()})
