from luna_bench.custom.types import AlgorithmName, ModelName

from .base_domain import BaseDomain
from .metric_result_domain import MetricResultDomain
from .registered_data_domain import RegisteredDataDomain


class MetricDomain(BaseDomain):
    name: str

    results: dict[ModelName, dict[AlgorithmName, MetricResultDomain]]

    config_data: RegisteredDataDomain
