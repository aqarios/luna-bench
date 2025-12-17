from __future__ import annotations

from pydantic import BaseModel

from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench.types import FeatureResult, ModelName


class FeatureResultUserModel(BaseModel):
    processing_time_ms: int
    model_name: ModelName

    status: JobStatus
    error: str | None
    result: FeatureResult | None
