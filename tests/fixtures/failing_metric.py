from luna_model import Solution

from luna_bench.base_components import BaseMetric
from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.helpers import metric
from luna_bench.types import MetricResult


class FakeMetricResult(MetricResult):
    """Failing metric result class."""

    random_number: int


@metric
class FailingMetric(BaseMetric):
    """Failing metric class."""

    def run(self, solution: Solution, feature_results: FeatureResults) -> MetricResult:  # noqa: ARG002
        """Failing metric which will return a random number."""
        msg = "Failing Metric because of Value Error"
        raise ValueError(msg)
