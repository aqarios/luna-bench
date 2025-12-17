from __future__ import annotations

from pydantic import BaseModel

from luna_bench.types import ModelName


class ModelMetadataUserModel(BaseModel):
    """
    Metadata for a model.

    A class that stores essential metadata about a model, including its ID,
    name, and hash value. Provides also access to the actual model.

    Attributes
    ----------
    id : int
        The unique identifier for the model.
    model_name : str
        The name of the model.
    model_hash : int
        The hash value of the model, used for identification and verification.
    """

    id: int
    name: ModelName
    hash: int
