from typing import Protocol

from returns.result import Result

from luna_bench._internal.entities.model_set.domain_models import ModelMetadataDomain


class ModelAllUc(Protocol):
    def __call__(self) -> Result[list[ModelMetadataDomain], str]:
        """A"""
