from .algorithm_domain import AlgorithmDomain
from .base_domain import BaseDomain
from .benchmark_status_enum import BenchmarkStatus
from .feature_domain import FeatureDomain
from .metric_domain import MetricDomain
from .modelset_domain import ModelSetDomain
from .plot_config_domain import PlotDomain


class BenchmarkDomain(BaseDomain):
    name: str

    status: BenchmarkStatus

    modelset: ModelSetDomain | None

    features: list[FeatureDomain]

    algorithms: list[AlgorithmDomain]

    metrics: list[MetricDomain]

    plots: list[PlotDomain]
