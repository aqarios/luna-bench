from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

from luna_quantum import Solution

from luna_bench.custom.base_results.metric_result import MetricResult
from luna_bench.custom.types import FeatureClass

from .meta_classes.metric_class_meta import MetricClassMeta
from .metric_direction_enum import MetricDirection
from .registerable_component import RegisterableComponent

if TYPE_CHECKING:
    from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer


class BaseMetric[TMetricResult: MetricResult = MetricResult](RegisterableComponent, ABC, metaclass=MetricClassMeta):
    """
    Base class for all metrics.

    A metric is a reusable component that extracts additional information about a solution. The result of each metric
    can be used plots to visualize it.

    A Metric must always be registered with the `@metric` decorator before it can be used in a benchmark.

    Attributes
    ----------
    required_features: ClassVar[list[FeatureClass]]
        The features this metric needs, set by the `@metric` decorator.
    direction: ClassVar[MetricDirection]
        Which end of this metric's scale is the better one, so that consumers that rank
        or plot metrics know which values to prefer. A metric meant to be compared across
        models should normalize the model away and declare an absolute direction, as the
        ratio metrics do; one that reports a raw objective value can only declare
        `MetricDirection.DEPENDS_ON_SENSE`. Defaults to `MetricDirection.INDIFFERENT`, so
        a metric that declares nothing is never mistaken for one with a genuine direction.
    """

    required_features: ClassVar[list[FeatureClass]]
    direction: ClassVar[MetricDirection] = MetricDirection.INDIFFERENT

    @abstractmethod
    def run(self, solution: Solution, feature_results: "FeatureResultContainer") -> TMetricResult:
        """
        Compute the metric value for a given solution.

        Parameters
        ----------
        solution: Solution
            The solution for which the metric should be computed.
        feature_results: FeatureResultContainer[T]
            If the metric requires additional features so it can be calculated, they will be provided here.

        Returns
        -------
        ArbitraryDataDomain
            The result of the computed metric.
        """
