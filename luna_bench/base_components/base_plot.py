from abc import ABC, abstractmethod
from typing import ClassVar

from pydantic import BaseModel

from luna_bench.base_components.data_types.benchmark_results import BenchmarkResults
from luna_bench.base_components.meta_classes.registered_class_meta import RegisteredClassMeta
from luna_bench.types import FeatureClass, MetricClass


class BasePlot(BaseModel, ABC, metaclass=RegisteredClassMeta):
    """
    Base interface for all plot components.

    Subclasses should implement the `run` method.

    """

    registered_id: ClassVar[str]

    required_features: ClassVar[list[FeatureClass]]
    required_metrics: ClassVar[list[MetricClass]]

    @abstractmethod
    def run(self, benchmark_results: BenchmarkResults) -> None: ...
