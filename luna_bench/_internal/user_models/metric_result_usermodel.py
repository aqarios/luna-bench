from __future__ import annotations

from pydantic import BaseModel

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.job_status_enum import JobStatus


class MetricResultUserModel(BaseModel):
    processing_time_ms: int
    model_name: str
    algorithm_name: str

    status: JobStatus
    error: str | None
    result: ArbitraryDataDomain | None
