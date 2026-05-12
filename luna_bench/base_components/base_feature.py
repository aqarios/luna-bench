from abc import ABC, abstractmethod

from luna_model import Model

from luna_bench.base_components.meta_classes.registered_class_meta import RegisteredClassMeta
from luna_bench.base_components.registerable_component import RegisterableComponent
from luna_bench.types import FeatureResult


class BaseFeature[TFeatureResult: FeatureResult = FeatureResult](
    RegisterableComponent,
    ABC,
    metaclass=RegisteredClassMeta,
):
    """
    Base class for all features.

    A feature is a reusable component that extracts additional information from a `Model`. The result of each feature
    can be used in metrics and in plots.

    A Feature must always be registered with the `@feature` decorator before it can be used in a benchmark.
    """

    @abstractmethod
    def run(self, model: Model) -> TFeatureResult:
        """
        Compute the feature value for a given model.

        Parameters
        ----------
        model: Model
            The model for which the feature should be computed.

        Returns
        -------
        TFeatureResult
            The result of the computed feature.
        """
