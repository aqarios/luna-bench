import random
from time import sleep
from typing import Any

from luna_quantum import Solution

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench.base_components import BaseMetric
from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.helpers import metric


class FakeMetricResult(ArbitraryDataDomain):
    """Fake feature result class."""

    random_number: int


@metric()
class FakeMetric(BaseMetric):
    """Fake metric class."""

    def run(self, solution: Solution, feature_results: FeatureResults[Any]) -> FakeMetricResult:  # noqa: ARG002
        """Fake metric which will return a random number."""
        sleep(0.1)
        return FakeMetricResult(
            random_number=random.randint(0, 100),  # noqa: S311
        )
