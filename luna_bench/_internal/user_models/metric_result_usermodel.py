from __future__ import annotations

from pydantic import BaseModel

from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench.types import MetricResult


class MetricResultUserModel(BaseModel):
    processing_time_ms: int
    model_name: str
    algorithm_name: str

    status: JobStatus
    error: str | None
    result: MetricResult | None
