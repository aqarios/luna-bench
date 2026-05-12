from typing import Any

from luna_bench.base_components import BaseMetric
from luna_bench.errors.components.metrics.metric_error import MetricError


class MetricResultWrongClassError(MetricError):
    """Error raised when a metric result has a wrong class for a specific metric class."""

    def __init__(self, metric_class: type[BaseMetric[Any]], allowed_classes: list[type[BaseMetric[Any]]]) -> None:
        super().__init__(
            f"Metric of the class {metric_class.__name__!r} is not allowed."
            f" Allowed classes are: {[c.__name__ for c in allowed_classes]}."
        )
