from __future__ import annotations

from pydantic import BaseModel

from luna_bench._internal.domain_models import JobStatus
from luna_bench._internal.interfaces.metric_i import IMetric
from luna_bench._internal.user_models.metric_result_usermodel import MetricResultUserModel


class MetricUserModel(BaseModel):
    name: str
    status: JobStatus

    metric: IMetric
    results: dict[tuple[str, str], MetricResultUserModel]  # key is the algorithm registered id and model name
