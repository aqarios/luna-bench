from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ModelMetadataDomain(BaseModel):
    model_id: int
    name: str
    hash: int

    model: Any = None
