from abc import abstractmethod

from pydantic import BaseModel
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench.base_components import BasePlot
from luna_bench.components.plots.generics.mixins.features_plot_mixin import FeaturesPlotMixin
from luna_bench.entities.benchmark_entity import BenchmarkEntity
from luna_bench.entities.feature_entity import FeatureEntity
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class FeaturesValidationResult(BaseModel):
    """
    Container for validated features data passed to plot run methods.

    Attributes
    ----------
    features : dict[str, FeatureEntity]
        Dictionary mapping feature names to feature instances. Contains only
        the features required by the plot.
    """

    features: dict[str, FeatureEntity]


class GenericFeaturesPlot(BasePlot[FeaturesValidationResult], FeaturesPlotMixin):
    """
    Base class for plots that only require features.

    Provides feature preparation and validation functionality.
    Subclasses must implement the run method.

    Attributes
    ----------
    features_names : ClassVar[set[str]]
        Set of required feature names for this plot.
    features: dict[str, FeatureEntity] | None
        Dictionary with features. It should contain features after validation process.
        At the moment when run method will be called it should contain needed featres.

    """

    @abstractmethod
    def run(self, data: FeaturesValidationResult) -> None:
        """
        Generate the plot using the provided features.

        This method must be implemented by subclasses to define the specific
        plotting logic for feature-based visualizations.

        Parameters
        ----------
        data : FeaturesValidationResult
            Validated features container. Access features via data.features,
            which contains only the features specified in the class's
            features_names attribute.

        Returns
        -------
        None
            The method should generate and save/display the plot as a side effect.

        """

    def validate_plot(
        self,
        benchmark: BenchmarkEntity,
    ) -> Result[FeaturesValidationResult, PlotRunError | UnknownLunaBenchError]:
        """
        Validate that required features are present in the benchmark.

        Parameters
        ----------
        benchmark: BenchmarkEntity
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

        return Success(FeaturesValidationResult(features=features.unwrap()))
