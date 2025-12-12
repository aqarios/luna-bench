from collections.abc import Mapping
from typing import overload

from pydantic import BaseModel, ConfigDict

from luna_bench.base_components.base_feature import BaseFeature
from luna_bench.types import FeatureConfig, FeatureName, FeatureResult

_NUM_KEYS = 2


class FeatureResults[T: BaseFeature](BaseModel):
    """Feature results container."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    allowed: tuple[type[T], ...] | None

    data: Mapping[type[T], Mapping[FeatureName, tuple[FeatureResult, FeatureConfig]]]

    def get_all(self, feature_cls: type[T]) -> Mapping[FeatureName, tuple[FeatureResult, FeatureConfig]]:
        if self.allowed is None:
            raise ValueError("Allowed features not set.")
        if feature_cls not in self.allowed:
            raise KeyError(  # TODO(Llewellyn): REPLACE WITH DEDICATED CLASS  # noqa: FIX002, TRY003
                f"Feature class {feature_cls.__name__!r} is not allowed. Allowed: {[c.__name__ for c in self.allowed]}"
            )
        return self.data.get(feature_cls, {})

    def get(self, feature_cls: type[T], feature_name: FeatureName) -> tuple[FeatureResult, FeatureConfig]:
        if self.allowed is None:
            raise ValueError("Allowed features not set.")
        if feature_cls not in self.allowed:
            raise KeyError(  # TODO(Llewellyn): REPLACE WITH DEDICATED CLASS  # noqa: FIX002, TRY003
                f"Feature class {feature_cls.__name__!r} is not allowed. Allowed: {[c.__name__ for c in self.allowed]}"
            )
        if feature_name not in self.data[feature_cls]:
            raise KeyError(  # TODO(Llewellyn): REPLACE WITH DEDICATED CLASS  # noqa: FIX002, TRY003
                f"Feature result not found for class={feature_cls.__name__!r}, id={feature_name!r}"
            )

        return self.data[feature_cls][feature_name]

    def first(self, feature_cls: type[T]) -> tuple[FeatureResult, FeatureConfig]:
        """
        Retrieve the first result for a given feature class.

        Parameters
        ----------
        feature_cls: type[T]
            The class for which the first result should be retrieved.

        Returns
        -------
        tuple[FeatureResult, FeatureConfig]
            A tuple containing the first feature result and its configuration for the given class.

        """
        return next(iter(self.get_all(feature_cls).values()))

    @overload
    def __getitem__(self, key: tuple[type[T], FeatureName]) -> tuple[FeatureResult, FeatureConfig]: ...

    @overload
    def __getitem__(self, key: type[T]) -> Mapping[FeatureName, tuple[FeatureResult, FeatureConfig]]: ...

    def __getitem__(
        self, key: tuple[type[T], FeatureName] | type[T]
    ) -> tuple[FeatureResult, FeatureConfig] | Mapping[FeatureName, tuple[FeatureResult, FeatureConfig]]:
        """
        Retrieve feature result by class and name, or all results for a class.

        If the key is a tuple, the results for the given class and feature name will be returned.
        If the key is only a class, all results for this class will be returned.

        Parameters
        ----------
        key: tuple[type[T], FeatureName] | type[T]
            The key used to retrieve the results. The feature class and the feature name or only the class.

        Results
        -------
        tuple[FeatureResult, FeatureConfig] | Mapping[FeatureName, tuple[FeatureResult, FeatureConfig]]
            The result contains a tuple of the feature result and its configuration. If the key is a class,
            a mapping of feature names to results will be returned. If the key is a tuple of class and feature name,
            only the result will be returned.
        """
        if isinstance(key, tuple) and len(key) == _NUM_KEYS:
            cls, feature_name = key
            return self.get(cls, feature_name=feature_name)
        return self.get_all(key)
