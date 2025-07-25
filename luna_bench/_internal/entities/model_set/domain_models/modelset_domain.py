from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from .model_metadata_domain import ModelMetadataDomain


class ModelSetDomain(BaseModel):
    id: int
    name: str
    models: list[ModelMetadataDomain]
