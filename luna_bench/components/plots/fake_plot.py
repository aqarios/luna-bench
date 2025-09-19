from luna_bench._internal.interfaces import IPlot
from luna_bench.helpers.decorators import plot


@plot
class FakePlot(IPlot):
    """Fake plot class."""

    def run(self) -> None: ...  # noqa: D102 # Not yet implemented
