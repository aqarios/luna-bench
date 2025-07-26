from __future__ import annotations

from pydantic import BaseModel

from .model_metadata_domain import ModelMetadataDomain


# ruff: noqa: TC001 Disable typing block rule since it will break pydantic.
class ModelSetDomain(BaseModel):
    """
    Domain model representing a set of models.

    A data class identified by an ID and name. It contains a list of model metadata objects representing the
    models in the set.

    Attributes
    ----------
    id : int
        The unique identifier for the model set.
    name : str
        The name of the model set.
    models : list[ModelMetadataDomain]
        A list of model metadata objects representing the models in this set.
    """

    id: int
    name: str
    models: list[ModelMetadataDomain]
