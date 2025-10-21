from typing import ClassVar

from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.interfaces.plot_i import IPlot
from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
from luna_bench._internal.user_models.feature_usermodel import FeatureUserModel
from luna_bench.errors.run_errors.plots_errors.features_missing_error import FeaturesMissingError
from luna_bench.errors.run_errors.plots_errors.plot_run_error import PlotRunError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class GenericFeaturesPlot(IPlot):
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

    features_names: ClassVar[set[str]] = set()
    features: dict[str, FeatureUserModel] | None = None

    def validate_plot(
        self,
        benchmark: BenchmarkUserModel,
    ) -> Result[None, PlotRunError | UnknownLunaBenchError]:
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

        self.features = features.unwrap()

        return Success(None)

    def _prepare_features(
        self,
        features: list[FeatureUserModel],
    ) -> Result[dict[str, FeatureUserModel], FeaturesMissingError | UnknownLunaBenchError]:
        """
        Parse features from benchmark and compare with config.

        Parameters
        ----------
        features : list[FeatureUserModel]
            List of benchmark's features.

        Returns
        -------
        Result[dict[str, IFeature], FeaturesMissingError | UnknownLunaBenchError]
            Success with dictionary mapping feature names to feature instances,
            or Failure with FeaturesMissingError if required features are missing.
        """
        result: dict[str, FeatureUserModel] = {}

        for feature in features:
            if feature.name in self.features_names:
                result[feature.name] = feature

        featires_diff = self.features_names - result.keys()

        if len(featires_diff) > 0:
            return Failure(FeaturesMissingError(list(featires_diff)))

        return Success(result)

    def has_feature(self, feature_name: str) -> bool:
        """
        Check if a feature is required by this plot.

        Parameters
        ----------
        feature_name : str
            Name of the feature to check.

        Returns
        -------
        bool
            True if the feature is in the required features set, False otherwise.
        """
        return feature_name in self.features_names

    def add_feature(self, feature_name: str) -> None:
        """
        Add feature manually to a plot configuration.

        Parameters
        ----------
        feature_name : str
            Name of the feature to add.
        """
        self.features_names.add(feature_name)
