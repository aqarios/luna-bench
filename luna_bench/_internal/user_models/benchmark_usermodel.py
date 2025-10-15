from __future__ import annotations

from pydantic import BaseModel

from .algorithm_usermodel import AlgorithmUserModel
from .feature_usermodel import FeatureUserModel
from .metric_usermodel import MetricUserModel
from .model_set_usermodel import ModelSetUserModel
from .plot_usermodel import PlotUserModel


class BenchmarkUserModel(BaseModel):
    name: str
    modelset: ModelSetUserModel | None

    features: list[FeatureUserModel]
    metrics: list[MetricUserModel]
    algorithms: list[AlgorithmUserModel]
    plots: list[PlotUserModel]
