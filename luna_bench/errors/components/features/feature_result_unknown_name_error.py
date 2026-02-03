from luna_bench.base_components.base_feature import BaseFeature
from luna_bench.errors.components.features.feature_error import FeatureError
from luna_bench.types import FeatureName


class FeatureResulUnknownNameError(FeatureError):
    """Error raised when a feature result has an unknown name for a specific feature class."""

    def __init__(
        self,
        feature_class: type[BaseFeature],
        feature_name: FeatureName,
        known_names: list[FeatureName],
    ) -> None:
        super().__init__(
            f"Feature of the class {feature_class.__name__!r} has unknown name '{feature_name}'."
            f"Currently there are {len(known_names)} known features: {', '.join(known_names)}."
        )
