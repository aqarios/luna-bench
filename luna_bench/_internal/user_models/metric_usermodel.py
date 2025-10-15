from __future__ import annotations

from pydantic import BaseModel

from luna_bench._internal.domain_models import JobStatus
from luna_bench._internal.interfaces.metric_i import IMetric


class MetricUserModel(BaseModel):
    name: str
    status: JobStatus

    metric: IMetric
