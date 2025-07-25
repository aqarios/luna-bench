from typing import Protocol

from luna_quantum import Model
from returns.result import Result

from luna_bench._internal.entities.model_set.domain_models import ModelSetDomain


class ModelSetCreateUc(Protocol):
    def __call__(self, modelset_name: str) -> Result[ModelSetDomain, str]:
        """Create a new model set with the given name."""


class ModelSetAddUc(Protocol):
    def __call__(self, dataset_id: int, model: Model) -> Result[ModelSetDomain, str]:
        """Add a model to the model set."""


class ModelSetListUc(Protocol):
    def __call__(self) -> Result[list[ModelSetDomain], str]:
        """List all model sets."""


class ModelSetRemoveUc(Protocol):
    def __call__(self, dataset_id: int, model: Model) -> Result[ModelSetDomain, str]:
        """Remove a model from the model set."""


class ModelSetDeleteUc(Protocol):
    def __call__(self, modelset_id: int) -> Result[None, str]:
        """Delete a model set."""
