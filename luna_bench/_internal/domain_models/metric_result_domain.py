from .arbitrary_data_domain import ArbitraryDataDomain
from .base_domain import BaseDomain
from .job_status_enum import JobStatus


class MetricResultDomain(BaseDomain):
    processing_time_ms: int  # time in ms
    model_name: str
    algorithm_registered_id: str

    status: JobStatus
    error: str | None
    result: ArbitraryDataDomain | None
