import random
from time import sleep

from luna_model import Solution

from luna_bench.custom import BaseMetric, metric
from luna_bench.custom.base_results.metric_result import MetricResult
from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer


class FakeMetricResult(MetricResult):
    """Fake feature result class."""

    random_number: int


@metric
class FakeMetric(BaseMetric[FakeMetricResult]):
    """Fake metric class."""

    def run(self, solution: Solution, feature_results: FeatureResultContainer) -> FakeMetricResult:  # noqa: ARG002
        """Fake metric which will return a random number."""
        sleep(0.1)
        return FakeMetricResult(
            random_number=random.randint(0, 100),  # noqa: S311
        )
