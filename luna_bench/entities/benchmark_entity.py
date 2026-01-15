from __future__ import annotations

from pydantic import BaseModel

from luna_bench.types import BenchmarkName

from .algorithm_entity import AlgorithmEntity
from .feature_entity import FeatureEntity
from .metric_entity import MetricEntity
from .model_set_entity import ModelSetEntity
from .plot_entity import PlotEntity


class BenchmarkEntity(BaseModel):
    """Represents a benchmark configuration with associated entities."""

    name: BenchmarkName
    modelset: ModelSetEntity | None

    features: list[FeatureEntity]
    metrics: list[MetricEntity]
    algorithms: list[AlgorithmEntity]
    plots: list[PlotEntity]
