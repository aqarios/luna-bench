from __future__ import annotations

from typing import Any

from pydantic import BaseModel, SkipValidation

from luna_bench.custom.base_components.base_algorithm_async import BaseAlgorithmAsync
from luna_bench.custom.base_components.base_algorithm_sync import BaseAlgorithmSync
from luna_bench.custom.types import AlgorithmName, ModelName

from .algorithm_result_entity import AlgorithmResultEntity


class AlgorithmEntity(BaseModel):
    """Represents a fully configured algorithm."""

    name: AlgorithmName

    algorithm: SkipValidation[BaseAlgorithmSync | BaseAlgorithmAsync[Any]]

    results: dict[ModelName, AlgorithmResultEntity]  # key is the model name
