from __future__ import annotations

from pydantic import BaseModel

from .model_metadata_domain import ModelMetadataDomain


# ruff: noqa: TC001 Disable typing block rule since it will break pydantic.
class ModelSetDomain(BaseModel):
    id: int
    name: str
    models: list[ModelMetadataDomain]
