from __future__ import annotations

from typing import Any

from pydantic import BaseModel, SkipValidation

from luna_bench._internal.domain_models import JobStatus
from luna_bench._internal.user_models.algorithm_result_usermodel import AlgorithmResultUserModel
from luna_bench.base_components import BaseAlgorithmAsync, BaseAlgorithmSync


class AlgorithmUserModel(BaseModel):
    name: str
    status: JobStatus

    algorithm: SkipValidation[BaseAlgorithmSync | BaseAlgorithmAsync[Any]]

    results: dict[str, AlgorithmResultUserModel]  # key is the model name
