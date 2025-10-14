from __future__ import annotations

from .algorithm_result_domain import AlgorithmResultDomain
from .base_domain import BaseDomain
from .job_status_enum import JobStatus
from .registered_data_domain import RegisteredDataDomain


class AlgorithmDomain(BaseDomain):
    name: str

    status: JobStatus

    result: AlgorithmResultDomain | None

    config_data: RegisteredDataDomain
