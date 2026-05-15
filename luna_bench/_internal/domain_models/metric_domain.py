from luna_bench.custom.types import AlgorithmName, ModelName
from luna_bench.entities.enums.job_status_enum import JobStatus

from .base_domain import BaseDomain
from .metric_result_domain import MetricResultDomain
from .registered_data_domain import RegisteredDataDomain


class MetricDomain(BaseDomain):
    name: str

    status: JobStatus
    results: dict[ModelName, dict[AlgorithmName, MetricResultDomain]]

    config_data: RegisteredDataDomain
