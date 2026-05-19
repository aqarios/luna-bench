from luna_model import Solution

from luna_bench.custom import BaseMetric, metric
from luna_bench.custom.base_results.metric_result import MetricResult
from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer


class FakeMetricResult(MetricResult):
    """Failing metric result class."""

    random_number: int


@metric
class FailingMetric(BaseMetric[MetricResult]):
    """Failing metric class."""

    def run(self, solution: Solution, feature_results: FeatureResultContainer) -> MetricResult:  # noqa: ARG002
        """Failing metric which will return a random number."""
        msg = "Failing Metric because of Value Error"
        raise ValueError(msg)
