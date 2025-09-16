from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .algorithm_result_domain import AlgorithmResultDomain
from .base_domain import BaseDomain
from .job_status_enum import JobStatus


class AlgorithmConfigDomain(BaseDomain):
    class Algorithm(BaseModel):
        model_config = ConfigDict(extra="allow")

    class Backend(BaseModel):
        model_config = ConfigDict(extra="allow")

    id: int
    name: str

    status: JobStatus

    result: AlgorithmResultDomain | None

    backend: AlgorithmConfigDomain.Backend | None
    algorithm: AlgorithmConfigDomain.Algorithm
