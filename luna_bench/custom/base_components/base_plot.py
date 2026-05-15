from abc import ABC, abstractmethod
from typing import ClassVar

from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.custom.types import FeatureClass, MetricClass

from .meta_classes.registered_class_meta import RegisteredClassMeta
from .registerable_component import RegisterableComponent


class BasePlot(RegisterableComponent, ABC, metaclass=RegisteredClassMeta):
    """
    Base interface for all plot components.

    Subclasses should implement the `run` method.

    """

    required_features: ClassVar[list[FeatureClass]]
    required_metrics: ClassVar[list[MetricClass]]

    @abstractmethod
    def run(self, benchmark_results: BenchmarkResultContainer) -> None:
        """Generate plot output from benchmark results.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Aggregated benchmark data consumed by the plot implementation.
        """
