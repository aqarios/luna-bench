from typing import Protocol

from luna_quantum import Model
from returns.result import Result

from luna_bench._internal.entities.model_set.domain_models import ModelSetDomain


class ModelSetCreateUc(Protocol):
    def __call__(self, modelset_name: str) -> Result[ModelSetDomain, Exception]:
        """Create a new model set with the given name."""


class ModelSetAddUc(Protocol):
    def __call__(self, dataset_id: int, model: Model) -> Result[ModelSetDomain, Exception]:
        """Add a model to the model set."""


class ModelSetListUc(Protocol):
    def __call__(self) -> Result[list[ModelSetDomain], Exception]:
        """List all model sets."""


class ModelSetRemoveUc(Protocol):
    def __call__(self, dataset_id: int, model: Model) -> Result[ModelSetDomain, Exception]:
        """Remove a model from the model set."""


class ModelSetDeleteUc(Protocol):
    def __call__(self, modelset_id: int) -> Result[None, Exception]:
        """Delete a model set."""
