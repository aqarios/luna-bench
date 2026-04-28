from abc import ABC, abstractmethod
from typing import ClassVar

from luna_bench.base_components.data_types.benchmark_results import BenchmarkResults
from luna_bench.base_components.meta_classes.registered_class_meta import RegisteredClassMeta
from luna_bench.base_components.registerable_component import RegisterableComponent
from luna_bench.types import FeatureClass, MetricClass


class BasePlot(RegisterableComponent, ABC, metaclass=RegisteredClassMeta):
    """
    Base interface for all plot components.

    Subclasses should implement the `run` method.

    """

    required_features: ClassVar[list[FeatureClass]]
    required_metrics: ClassVar[list[MetricClass]]

    @abstractmethod
    def run(self, benchmark_results: BenchmarkResults) -> None:
        """Generate plot output from benchmark results.

        Parameters
        ----------
        benchmark_results : BenchmarkResults
            Aggregated benchmark data consumed by the plot implementation.
        """
