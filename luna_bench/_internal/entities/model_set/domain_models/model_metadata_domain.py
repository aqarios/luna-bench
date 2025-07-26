from typing import Any

from pydantic import BaseModel


class ModelMetadataDomain(BaseModel):
    """
    Domain model representing metadata for a model.

    A data class that encapsulates the essential metadata about a model,
    including its identifier, name, and hash value. Optionally can include
    a reference to the actual model.

    Attributes
    ----------
    id : int
        The unique identifier for the model.
    name : str
        The name of the model.
    hash : int
        The hash value of the model, used for identification and verification.
    model : Any, optional
        A reference to the actual model object, by default None.
    """

    id: int
    name: str
    hash: int

    model: Any = None
