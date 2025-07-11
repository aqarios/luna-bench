from __future__ import annotations

from pydantic import BaseModel

from .model_metadata_domain import ModelMetadataDomain


class ModelSetDomain(BaseModel):
    modelset_id: int
    name: str
    models: list[ModelMetadataDomain]
