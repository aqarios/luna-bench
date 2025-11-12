import random
from time import sleep

from luna_quantum import Solution

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import IMetric
from luna_bench.helpers import metric


class FakeMetricResult(ArbitraryDataDomain):
    """Fake feature result class."""

    random_number: int


@metric
class FakeMetric(IMetric):
    """Fake metric class."""

    def run(self, solution: Solution) -> FakeMetricResult:
        sleep(0.1)
        return FakeMetricResult(
            random_number=random.randint(0, 100),
        )
