from __future__ import annotations

from pydantic import BaseModel

from luna_bench.custom import BaseMetric
from luna_bench.custom.types import AlgorithmName, MetricName, ModelName
from luna_bench.entities.metric_result_entity import MetricResultEntity


class MetricEntity(BaseModel):
    """Represents a fully configured metric."""

    name: MetricName

    metric: BaseMetric
    results: dict[ModelName, dict[AlgorithmName, MetricResultEntity]]
