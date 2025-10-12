from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from luna_bench._internal.domain_models.job_status_enum import JobStatus


class FeatureResultUserModel(BaseModel):
    processing_time_ms: int
    model_name: str

    status: JobStatus
    error: str | None
    result: dict[str, Any] | None
