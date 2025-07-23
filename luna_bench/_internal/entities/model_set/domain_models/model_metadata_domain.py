from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ModelMetadataDomain(BaseModel):
    id: int
    name: str
    hash: int

    model: Any = None
