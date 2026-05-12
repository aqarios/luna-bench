"""Average approximation ratio per solver bar chart."""

from __future__ import annotations

from luna_bench.base_components.data_types.benchmark_results import BenchmarkResults
from luna_bench.components.metrics.approximation_ratio import ApproximationRatio
from luna_bench.components.plots.generics.bar_plot import BarPlot
from luna_bench.helpers.decorators import plot


@plot(ApproximationRatio)
class AverageApproximationRatioPlot(BarPlot):
    """Bar chart showing average approximation ratio per algorithm.

    Examples
    --------
    >>> bench.add_metric(name="approx_ratio", metric=ApproximationRatio())
    >>> bench.add_plot(name="avg_approx", plot=AverageApproximationRatioPlot())
    """

    def run(self, benchmark_results: BenchmarkResults) -> None:
        """Generate plot output from benchmark results.

        Parameters
        ----------
        benchmark_results : BenchmarkResults
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
