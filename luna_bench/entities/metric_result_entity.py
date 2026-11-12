from __future__ import annotations

from pydantic import BaseModel

from luna_bench.custom.base_results.metric_result import MetricResult

from .enums import JobStatus


class MetricResultEntity(BaseModel):
    """Represents the result of a metric."""

    processing_time_ms: int
    model_name: str
    algorithm_name: str

    #: The run of the algorithm this metric was computed on, counted from 0.
    repetition: int = 0

    status: JobStatus
    error: str | None
    result: MetricResult | None
