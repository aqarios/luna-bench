from __future__ import annotations

from pydantic import BaseModel

from luna_bench._internal.domain_models import JobStatus
from luna_bench._internal.user_models.metric_result_usermodel import MetricResultUserModel
from luna_bench.base_components import BaseMetric


class MetricUserModel(BaseModel):
    name: str
    status: JobStatus

    metric: BaseMetric
    results: dict[tuple[str, str], MetricResultUserModel]  # key is the algorithm registered id and model name
