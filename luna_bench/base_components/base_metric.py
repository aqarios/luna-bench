from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar

from luna_quantum import Solution
from pydantic import BaseModel

from luna_bench.types import FeatureClass, MetricResult

from .meta_classes.metric_class_meta import MetricClassMeta

if TYPE_CHECKING:
    from luna_bench.base_components.data_types.feature_results import FeatureResults


class BaseMetric(BaseModel, ABC, metaclass=MetricClassMeta):
    """
    Base class for all metrics.

    A metric is a reusable component that extracts additional information about a solution. The result of each metric
    can be used plots to visualize it.

    A Metric must always be registered with the `@metric` decorator before it can be used in a benchmark.
    """

    registered_id: ClassVar[str]
    required_features: ClassVar[list[FeatureClass]]

    @abstractmethod
    def run(self, solution: Solution, feature_results: "FeatureResults") -> MetricResult:
        """
        Compute the metric value for a given solution.

        Parameters
        ----------
        solution: Solution
            The solution for which the metric should be computed.
        feature_results: FeatureResults[T]
            If the metric requires additional features so it can be calculated, they will be provided here.

        Returns
        -------
        ArbitraryDataDomain
            The result of the computed metric.
        """
