"""Average feasibility ratio per solver bar chart."""

from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench.custom import plot
from luna_bench.metrics.feasbility_ratio import FeasibilityRatio
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer


@plot(FeasibilityRatio)
class AverageFeasibilityRatioPlot(BarPlot):
    """Bar chart showing average feasibility ratio per algorithm.

    Examples
    --------
    >>> bench.add_metric(name="feasibility", metric=FeasibilityRatio())
    >>> bench.add_plot(name="avg_feasibility", plot=AverageFeasibilityRatioPlot())
    """

    def run(self, benchmark_results: BenchmarkResultContainer) -> None:
        """Generate plot output from benchmark results.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Aggregated benchmark data consumed by the plot implementation.
        """
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
