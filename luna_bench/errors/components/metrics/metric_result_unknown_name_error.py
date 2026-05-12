from luna_bench.base_components import BaseMetric
from luna_bench.errors.components.metrics.metric_error import MetricError
from luna_bench.types import MetricName


class MetricResulUnknownNameError(MetricError):
    """Error raised when a metric result has an unknown name for a specific metric class."""

    def __init__(
        self,
        metric_class: type[BaseMetric],
        metric_name: MetricName,
        known_names: list[MetricName],
    ) -> None:
        super().__init__(
            f"Metric of the class {metric_class.__name__!r} has unknown name '{metric_name}'."
            f"Currently there are {len(known_names)} known metrics: {', '.join(known_names)}."
        )
