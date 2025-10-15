from luna_bench._internal.interfaces import IMetric
from luna_bench.helpers import metric


@metric
class FakeMetric(IMetric):
    """Fake metric class."""
