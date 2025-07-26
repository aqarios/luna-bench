from typing import Protocol

from luna_bench._internal.entities.model_set.domain_models import ModelMetadataDomain


class ModelAllUc(Protocol):
    """Protocol for retrieving all models."""

    def __call__(self) -> list[ModelMetadataDomain]:
        """
        Retrieve all models from storage.

        Returns
        -------
        list[ModelMetadataDomain]
            A list of all model metadata domain objects.
        """
        ...
