from __future__ import annotations

from pydantic import BaseModel

from luna_bench.types import ModelSetName

from .model_metadata_entity import ModelMetadataEntity


class ModelSetEntity(BaseModel):
    """
    Set of models.

    Represents a collection of models with operations for creating, loading, adding,
    removing, and deleting models.

    Attributes
    ----------
    id : int
        The unique identifier for the model set.
    name : str
        The name of the model set.
    models : list[ModelData]
        A list of ModelData objects representing the models in this set.
    """

    id: int
    name: ModelSetName
    models: list[ModelMetadataEntity]
