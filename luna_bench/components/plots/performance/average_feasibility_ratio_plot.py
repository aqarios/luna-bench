"""Average feasibility ratio per solver bar chart."""

from __future__ import annotations

from luna_bench.base_components.data_types.benchmark_results import BenchmarkResults
from luna_bench.components.metrics.feasbility_ratio import FeasibilityRatio
from luna_bench.components.plots.generics.bar_plot import BarPlot
from luna_bench.helpers.decorators import plot


@plot(required_metrics=FeasibilityRatio)
class AverageFeasibilityRatioPlot(BarPlot):
    """Bar chart showing average feasibility ratio per algorithm.

    Examples
    --------
    >>> bench.add_metric(name="feasibility", metric=FeasibilityRatio())
    >>> bench.add_plot(name="avg_feasibility", plot=AverageFeasibilityRatioPlot())
    """

    def run(self, benchmark_results: BenchmarkResults) -> None:
        rows = [
            {
                "algorithm": algorithm_name,
                "model": model_name,
                "feasibility_ratio": metric_result.feasibility_ratio,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(FeasibilityRatio)
        ]

        self.create(
            rows=rows,
            x="algorithm",
            y="feasibility_ratio",
            xlabel="Algorithm",
            title="Average Feasibility Ratio per Solver",
            ylabel="Feasibility Ratio",
            ylim=(0, 1.15),
            hline=1.0,
            hline_label="Upper Limit (1.0)",
        )
