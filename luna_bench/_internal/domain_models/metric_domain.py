from luna_bench.entities.enums.job_status_enum import JobStatus

from .base_domain import BaseDomain
from .metric_result_domain import MetricResultDomain
from .registered_data_domain import RegisteredDataDomain


class MetricDomain(BaseDomain):
    name: str

    status: JobStatus
    results: dict[tuple[str, str], MetricResultDomain]  # key is the solver registered id and model name

    config_data: RegisteredDataDomain
