from __future__ import annotations

from typing import Any

from pydantic import BaseModel, SkipValidation

from luna_bench._internal.domain_models import JobStatus
from luna_bench._internal.user_models.algorithm_result_usermodel import AlgorithmResultUserModel
from luna_bench.base_components.base_algorithm_async import BaseAlgorithmAsync
from luna_bench.base_components.base_algorithm_sync import BaseAlgorithmSync
from luna_bench.types import AlgorithmName, ModelName


class AlgorithmUserModel(BaseModel):
    name: AlgorithmName
    status: JobStatus

    algorithm: SkipValidation[BaseAlgorithmSync | BaseAlgorithmAsync[Any]]

    results: dict[ModelName, AlgorithmResultUserModel]  # key is the model name
