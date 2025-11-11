from __future__ import annotations

from .algorithm_result_domain import AlgorithmResultDomain
from .algorithm_type_enum import AlgorithmType
from .base_domain import BaseDomain
from .job_status_enum import JobStatus
from .registered_data_domain import RegisteredDataDomain


class AlgorithmDomain(BaseDomain):
    name: str

    status: JobStatus

    algorithm_type: AlgorithmType
    results: dict[str, AlgorithmResultDomain]  # key is the model name

    config_data: RegisteredDataDomain
