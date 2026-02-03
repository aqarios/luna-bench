from luna_bench.base_components.base_feature import BaseFeature
from luna_bench.errors.components.features.feature_error import FeatureError


class FeatureResultWrongClassError(FeatureError):
    """Error raised when a feature result has a wrong class for a specific feature class."""

    def __init__(self, feature_class: type[BaseFeature], allowed_classes: list[type[BaseFeature]]) -> None:
        super().__init__(
            f"Feature of the class {feature_class.__name__!r} is not allowed."
            f" Allowed classes are: {[c.__name__ for c in allowed_classes]}."
        )
