from __future__ import annotations

from pydantic import BaseModel

from luna_bench.types import MetricResult

from .enums import JobStatus


class MetricResultEntity(BaseModel):
    """Represents the result of a metric."""

    processing_time_ms: int
    model_name: str
    algorithm_name: str

    status: JobStatus
    error: str | None
    result: MetricResult | None
