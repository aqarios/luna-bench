from .base_domain import BaseDomain
from .job_status_enum import JobStatus
from .metric_result_domain import MetricResultDomain
from .registered_data_domain import RegisteredDataDomain


class MetricDomain(BaseDomain):
    name: str

    status: JobStatus
    result: MetricResultDomain | None

    config_data: RegisteredDataDomain
