from __future__ import annotations

from luna_quantum.solve.interfaces.algorithm_i import (
    IAlgorithm,
)
from luna_quantum.solve.interfaces.backend_i import IBackend
from pydantic import BaseModel

from luna_bench._internal.domain_models import JobStatus


class AlgorithmUserModel(BaseModel):
    name: str
    status: JobStatus

    algorithm: IAlgorithm[IBackend]
