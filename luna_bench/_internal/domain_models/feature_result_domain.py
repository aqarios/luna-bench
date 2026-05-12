from luna_bench.entities.enums.job_status_enum import JobStatus

from .arbitrary_data_domain import ArbitraryDataDomain
from .base_domain import BaseDomain


class FeatureResultDomain(BaseDomain):
    processing_time_ms: int  # time in ms
    model_name: str

    status: JobStatus
    error: str | None
    result: ArbitraryDataDomain | None
