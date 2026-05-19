from luna_bench.custom import BaseMetric
from luna_bench.custom.types import MetricName
from luna_bench.errors.components.metrics.metric_error import MetricError


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
