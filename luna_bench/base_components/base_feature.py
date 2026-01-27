from abc import ABC, abstractmethod
from typing import ClassVar

from luna_quantum import Model
from pydantic import BaseModel

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.base_components.meta_classes.registered_class_meta import RegisteredClassMeta


class BaseFeature(BaseModel, ABC, metaclass=RegisteredClassMeta):
    """
    Base class for all features.

    A feature is a reusable component that extracts additional information from a `Model`. The result of each feature
    can be used in metrics and in plots.

    A Feature must always be registered with the `@feature` decorator before it can be used in a benchmark.
    """

    registered_id: ClassVar[str]

    @abstractmethod
    def run(self, model: Model) -> ArbitraryDataDomain:
        """
        Compute the feature value for a given model.

        Parameters
        ----------
        model: Model
            The model for which the feature should be computed.

        Returns
        -------
        ArbitraryDataDomain
            The result of the computed feature.
        """
