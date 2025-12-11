from __future__ import annotations

from typing import Any

from pydantic import BaseModel, SkipValidation

from luna_bench._internal.domain_models import JobStatus
from luna_bench._internal.interfaces.algorithm_async import AlgorithmAsync
from luna_bench._internal.interfaces.algorithm_sync import AlgorithmSync
from luna_bench._internal.user_models.algorithm_result_usermodel import AlgorithmResultUserModel


class AlgorithmUserModel(BaseModel):
    name: str
    status: JobStatus

    algorithm: SkipValidation[AlgorithmSync | AlgorithmAsync[Any]]

    results: dict[str, AlgorithmResultUserModel]  # key is the model name
