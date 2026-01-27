from collections.abc import Mapping
from typing import overload

from pydantic import BaseModel, ConfigDict

from luna_bench.base_components.base_feature import BaseFeature
from luna_bench.errors.components.features.feature_result_unknown_name_error import FeatureResulUnknownNameError
from luna_bench.errors.components.features.feature_result_wrong_class_error import FeatureResultWrongClassError
from luna_bench.types import FeatureName, FeatureResult

_NUM_KEYS = 2


class FeatureResults(BaseModel):
    """Feature results container."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    allowed: list[type[BaseFeature]]

    data: Mapping[type[BaseFeature], Mapping[FeatureName, tuple[FeatureResult, BaseFeature]]]

    def get_all(self, feature_cls: type[BaseFeature]) -> Mapping[FeatureName, tuple[FeatureResult, BaseFeature]]:
        """
        Get all results for a given feature class.

        Parameters
        ----------
        feature_cls : type[BaseFeature]
            The feature class to retrieve results for.

        Returns
        -------
        Mapping[FeatureName, tuple[FeatureResult, BaseFeature]]
            A mapping of feature names to their corresponding results and configurations.

        Raises
        ------
        FeatureResultWrongClassError
            If the provided feature class is not allowed in this FeatureResults instance.
        """
        if feature_cls not in self.allowed:
            raise FeatureResultWrongClassError(feature_cls, self.allowed)
        return self.data.get(feature_cls, {})

    def get(self, feature_cls: type[BaseFeature], feature_name: FeatureName) -> tuple[FeatureResult, BaseFeature]:
        """
        Get a single result for a given feature class and name.

        Parameters
        ----------
        feature_cls : type[BaseFeature]
            The feature class to retrieve the result for.
        feature_name : FeatureName
            The name of the feature to retrieve the result for.

        Returns
        -------
        tuple[FeatureResult, BaseFeature]
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

    def first(self, feature_cls: type[BaseFeature]) -> tuple[FeatureResult, BaseFeature]:
        """
        Retrieve the first result for a given feature class.

        Parameters
        ----------
        feature_cls: type[BaseFeature]
            The class for which the first result should be retrieved.

        Returns
        -------
        tuple[FeatureResult, BaseFeature]
            A tuple containing the first feature result and its configuration for the given class.

        """
        return next(iter(self.get_all(feature_cls).values()))

    @overload
    def __getitem__(self, key: tuple[type[BaseFeature], FeatureName]) -> tuple[FeatureResult, BaseFeature]: ...

    @overload
    def __getitem__(self, key: type[BaseFeature]) -> Mapping[FeatureName, tuple[FeatureResult, BaseFeature]]: ...

    def __getitem__(
        self, key: tuple[type[BaseFeature], FeatureName] | type[BaseFeature]
    ) -> tuple[FeatureResult, BaseFeature] | Mapping[FeatureName, tuple[FeatureResult, BaseFeature]]:
        """
        Retrieve feature result by class and name, or all results for a class.

        If the key is a tuple, the results for the given class and feature name will be returned.
        If the key is only a class, all results for this class will be returned.

        Parameters
        ----------
        key: tuple[type[BaseFeature], FeatureName] | type[BaseFeature]
            The key used to retrieve the results. The feature class and the feature name or only the class.

        Results
        -------
        tuple[FeatureResult, BaseFeature] | Mapping[FeatureName, tuple[FeatureResult, BaseFeature]]
            The result contains a tuple of the feature result and its configuration. If the key is a class,
            a mapping of feature names to results will be returned. If the key is a tuple of class and feature name,
            only the result will be returned.
        """
        if isinstance(key, tuple) and len(key) == _NUM_KEYS:
            cls, feature_name = key
            return self.get(cls, feature_name=feature_name)
        if isinstance(key, type):
            return self.get_all(key)
        return {}
