from __future__ import annotations

from pydantic import BaseModel

from luna_bench.base_components import BaseMetric
from luna_bench.entities.metric_result_entity import MetricResultEntity
from luna_bench.types import AlgorithmName, MetricName, ModelName

from .enums import JobStatus


class MetricEntity(BaseModel):
    """Represents a fully configured metric."""

    name: MetricName
    status: JobStatus

    metric: BaseMetric
    results: dict[ModelName, dict[AlgorithmName, MetricResultEntity]]
