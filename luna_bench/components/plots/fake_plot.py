import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from luna_bench.components.metrics.fake_metric import FakeMetric, FakeMetricResult
from luna_bench.components.plots.generics.features_metrics_plot import (
    FeaturesAndMetricsValidationResult,
    GenericFeaturesMetricsPlot,
)
from luna_bench.components.plots.generics.metrics_plot import GenericMetricsPlot, MetricsValidationResult
from luna_bench.components.plots.utils.style import PALETTE
from luna_bench.helpers.decorators import plot


@plot(metrics_ids=("test",), features_ids=("test",))
class FakePlot(GenericFeaturesMetricsPlot):  # type: ignore[call-arg]
    """
    Fake plot implementation for testing purposes.

    This plot requires a metric named 'test' and a feature named 'test'.
    Used primarily for testing the plot infrastructure.
    """

    def run(self, data: FeaturesAndMetricsValidationResult) -> None:
        """Execute the fake plot generation."""


@plot(metrics_ids=(FakeMetric.registered_id,))
class FakeMetricAveragePerSolverPlot(GenericMetricsPlot):  # type: ignore[call-arg]
    """Bar chart showing the average FakeMetric value per algorithm.

    Groups all (algorithm, model) results by algorithm, computes the
    mean ``random_number`` for each, and draws a bar chart.

    Examples
    --------
    >>> bench.add_metric(name="fake", metric=FakeMetric())
    >>> bench.add_plot(name="avg_per_solver", plot=FakeMetricAveragePerSolverPlot())
    """

    def run(self, data: MetricsValidationResult) -> None:
        """Plot average FakeMetric random_number per solver as a bar chart."""
        metric_entity = data.metrics[FakeMetric.registered_id]

        rows = []
        for (algorithm_name, model_name), result in metric_entity.results.items():
            if result.result is not None:
                parsed = FakeMetricResult.model_validate(result.result.model_dump())
                rows.append({"algorithm": algorithm_name, "model": model_name, "random_number": parsed.random_number})

        df = pd.DataFrame(rows)

        plt.figure(figsize=(8, 5))
        sns.barplot(data=df, x="algorithm", y="random_number", errorbar="sd", palette=PALETTE)
        plt.ylabel("Average random_number")
        plt.xlabel("Algorithm")
        plt.title("Average FakeMetric Value per Solver")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.show()
