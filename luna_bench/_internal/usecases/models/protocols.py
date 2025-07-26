from typing import Protocol

from luna_bench._internal.entities.model_set.domain_models import ModelMetadataDomain


class ModelAllUc(Protocol):
    def __call__(self) -> list[ModelMetadataDomain]: ...
