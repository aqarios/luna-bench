import random
from time import sleep

from luna_quantum import Solution

from luna_bench.base_components import BaseMetric
from luna_bench.base_components.data_types.arbitrary_data import ArbitraryData
from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.helpers import metric


class FakeMetricResult(ArbitraryData):
    """Fake feature result class."""

    random_number: int


@metric
class FakeMetric(BaseMetric):
    """Fake metric class."""

    def run(self, solution: Solution, feature_results: FeatureResults) -> FakeMetricResult:  # noqa: ARG002
        """Fake metric which will return a random number."""
        sleep(0.1)
        return FakeMetricResult(
            random_number=random.randint(0, 100),  # noqa: S311
        )
