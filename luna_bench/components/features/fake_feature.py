from luna_bench._internal.interfaces import IFeature
from luna_bench.helpers import feature


@feature
class FakeFeature(IFeature):
    """Fake feature class."""

    def run(self) -> None:  # noqa: D102 # Not yet implemented
        raise NotImplementedError
