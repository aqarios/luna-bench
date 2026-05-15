from __future__ import annotations

from pydantic import BaseModel

from luna_bench.custom.base_results.feature_result import FeatureResult
from luna_bench.custom.types import ModelName

from .enums import JobStatus


class FeatureResultEntity(BaseModel):
    """Represents the result of a feature."""

    processing_time_ms: int
    model_name: ModelName

    status: JobStatus
    error: str | None
    result: FeatureResult | None
