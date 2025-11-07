from luna_bench._internal.user_models.feature_usermodel import FeatureUserModel
from luna_bench._internal.user_models.metric_usermodel import MetricUserModel
from luna_bench.components.plots.generics.features_metrics_plot import GenericFeaturesMetricsPlot
from luna_bench.helpers.decorators import plot


@plot(metrics=("test",), features=("test",))
class FakePlot(GenericFeaturesMetricsPlot):  # type: ignore[call-arg]
    """
    Fake plot implementation for testing purposes.

    This plot requires a metric named 'test' and a feature named 'test'.
    Used primarily for testing the plot infrastructure.
    """

    def run(self, metrics: dict[str, MetricUserModel], features: dict[str, FeatureUserModel]) -> None:
        """Execute the fake plot generation."""
