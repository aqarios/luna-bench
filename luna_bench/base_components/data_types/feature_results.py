from __future__ import annotations

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict

from luna_bench.errors.components.features.feature_result_unknown_name_error import FeatureResulUnknownNameError
from luna_bench.errors.components.features.feature_result_wrong_class_error import FeatureResultWrongClassError
from luna_bench.types import FeatureClass, FeatureComputed, FeatureName, FeatureResult


class FeatureResults(BaseModel):
    """Feature results container."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    allowed: list[FeatureClass]  # TODO MAYBE REMOVE IT we kind of already check it when creating this container

    data: Mapping[FeatureClass, Mapping[FeatureName, FeatureComputed]]

    def get_all(self, feature_cls: FeatureClass) -> Mapping[FeatureName, FeatureResult]:
        """Get all results for a class."""
        return {name: result[0] for name, result in self.get_all_with_config(feature_cls=feature_cls).items()}

    def get_all_with_config(self, feature_cls: FeatureClass) -> Mapping[FeatureName, FeatureComputed]:
        """
        Get all results for a given feature class.

        Parameters
        ----------
        feature_cls : FeatureClass
            The feature class to retrieve results for.

        Returns
        -------
        Mapping[FeatureName, FeatureComputed]
            A mapping of feature names to their corresponding results and configurations.

        Raises
        ------
        FeatureResultWrongClassError
            If the provided feature class is not allowed in this FeatureResults instance.
        """
        if feature_cls not in self.allowed:
            raise FeatureResultWrongClassError(feature_cls, self.allowed)
        return self.data.get(feature_cls, {})

    def get(self, feature_cls: FeatureClass, feature_name: FeatureName) -> FeatureResult:
        """
        Get a single result for a given feature class and name.

        Parameters
        ----------
        feature_cls : FeatureClass
            The feature class to retrieve the result for.
        feature_name : FeatureName
            The name of the feature to retrieve the result for.

        Returns
        -------
        FeatureResult
            The result for the specified feature (without configuration).

        Raises
        ------
        FeatureResultWrongClassError
            If the provided feature class is not allowed.
        FeatureResulUnknownNameError
            If the provided feature name is not found for the given class.
        """
        return self.get_with_config(feature_cls=feature_cls, feature_name=feature_name)[0]

    def get_with_config(self, feature_cls: FeatureClass, feature_name: FeatureName) -> FeatureComputed:
        """
        Get a single result for a given feature class and name.

        Parameters
        ----------
        feature_cls : FeatureClass
            The feature class to retrieve the result for.
        feature_name : FeatureName
            The name of the feature to retrieve the result for.

        Returns
        -------
        FeatureComputed
            The result and configuration for the specified feature.

        Raises
        ------
        FeatureResultWrongClassError
            If the provided feature class is not allowed.
        FeatureResulUnknownNameError
            If the provided feature name is not found for the given class.

        """
        if feature_cls not in self.allowed:
            raise FeatureResultWrongClassError(feature_cls, self.allowed)
        if feature_name not in self.data[feature_cls]:
            raise FeatureResulUnknownNameError(
                feature_class=feature_cls, feature_name=feature_name, known_names=list(self.data[feature_cls].keys())
            )

        return self.data[feature_cls][feature_name]

    def first(self, feature_cls: FeatureClass) -> FeatureResult:
        """
        Retrieve the first result for a given feature class.

        Parameters
        ----------
        feature_cls: FeatureClass
            The class for which the first result should be retrieved.

        Returns
        -------
        FeatureResult
            The first feature result for the given class (without configuration).

        Raises
        ------
        FeatureResultWrongClassError
            If the provided feature class is not allowed.
        """
        return self.first_with_config(feature_cls=feature_cls)[0]

    def first_with_config(self, feature_cls: FeatureClass) -> FeatureComputed:
        """
        Retrieve the first result with its configuration for a given feature class.

        Parameters
        ----------
        feature_cls: FeatureClass
            The class for which the first result should be retrieved.

        Returns
        -------
        FeatureComputed
            A tuple containing the first feature result and its configuration for the given class.

        Raises
        ------
        FeatureResultWrongClassError
            If the provided feature class is not allowed.
        """
        return next(iter(self.get_all_with_config(feature_cls).values()))
