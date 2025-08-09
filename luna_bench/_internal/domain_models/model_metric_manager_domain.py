from pydantic import BaseModel

from .model_metric_domain import ModelMetricDomain


class ModelMetricManagerDomain(BaseModel):
    benchmark_id: int

    model_metrics: list[ModelMetricDomain] = []
