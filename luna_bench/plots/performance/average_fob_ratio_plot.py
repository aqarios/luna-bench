"""Average fraction of overall best solution per solver bar chart."""

from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench.custom import plot
from luna_bench.metrics.fraction_of_overall_best_solution import FractionOfOverallBestSolution
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer


@plot(FractionOfOverallBestSolution)
class AverageFoBRatioPlot(BarPlot):
    """Bar chart showing average fraction of overall best per algorithm.

    Examples
    --------
    >>> bench.add_metric(name="fob", metric=FractionOfOverallBestSolution())
    >>> bench.add_plot(name="avg_fob", plot=AverageFoBRatioPlot())
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
                "fraction_of_overall_best": metric_result.fraction_of_overall_best_solution,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(
                FractionOfOverallBestSolution
            )
        ]

        self.create(
            rows=rows,
            x="algorithm",
            y="fraction_of_overall_best",
            xlabel="Algorithm",
            ylabel="Fraction of overall best solution",
            title="Average Fraction of overall best Ratio per Solver (1.0 = optimal)",
            hline=1.0,
            hline_label="Optimal (1.0)",
        )
