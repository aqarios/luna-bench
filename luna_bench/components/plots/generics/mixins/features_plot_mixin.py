"""Mixin providing features validation and management for plot components."""

from typing import ClassVar

from returns.result import Failure, Result, Success

from luna_bench._internal.user_models.feature_usermodel import FeatureUserModel
from luna_bench.errors.run_errors.plots_errors.features_missing_error import FeaturesMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class FeaturesPlotMixin:
    """
    Mixin that adds features validation and management capabilities to plot classes.

    This mixin provides functionality to validate that required features are present
    in a benchmark configuration and to manage the set of features needed by a plot.

    Attributes
    ----------
    features_names : set[str]
        Class-level set of feature names required by the plot.

    Methods
    -------
    _prepare_features(features)
        Validate and map benchmark features against required features.
    add_feature(feature_name)
        Manually add a feature to the required features set.
    has_feature(feature_name)
        Check if a feature is in the required features set.
    """

    features_names: ClassVar[set[str]] = set()

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
