from luna_bench.components.plots.generics.features_metrics_plot import (
    FeaturesAndMetricsValidationResult,
    GenericFeaturesMetricsPlot,
)
from luna_bench.helpers.decorators import plot


@plot(metrics=("test",), features=("test",))
class FakePlot(GenericFeaturesMetricsPlot):  # type: ignore[call-arg]
    """
    Fake plot implementation for testing purposes.

    This plot requires a metric named 'test' and a feature named 'test'.
    Used primarily for testing the plot infrastructure.
    """

    def run(self, data: FeaturesAndMetricsValidationResult) -> None:
        """Execute the fake plot generation."""
