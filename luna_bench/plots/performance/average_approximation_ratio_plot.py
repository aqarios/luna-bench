"""Average approximation ratio per solver bar chart."""

from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench.custom import plot
from luna_bench.metrics.approximation_ratio import ApproximationRatio
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer


@plot(ApproximationRatio)
class AverageApproximationRatioPlot(BarPlot):
    """Bar chart showing average approximation ratio per algorithm.

    Examples
    --------
    >>> bench.add_metric(name="approx_ratio", metric=ApproximationRatio())
    >>> bench.add_plot(name="avg_approx", plot=AverageApproximationRatioPlot())
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
                "approximation_ratio": metric_result.approximation_ratio,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(
                ApproximationRatio
            )
        ]

        self.create(
            rows=rows,
            x="algorithm",
            y="approximation_ratio",
            xlabel="Algorithm",
            ylabel="Approximation Ratio",
            title="Average Approximation Ratio per Solver (1.0 = optimal)",
            hline=1.0,
            hline_label="Optimal (1.0)",
        )
