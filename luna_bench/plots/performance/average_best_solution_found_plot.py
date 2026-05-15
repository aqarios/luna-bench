"""Average best solution found per solver bar chart."""

from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench.custom import plot
from luna_bench.metrics.fraction_of_overall_best_solution import FractionOfOverallBestSolution
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer


@plot(FractionOfOverallBestSolution)
class AverageBestSolutionFoundRatioPlot(BarPlot):
    """Bar chart showing average best solution found ratio per algorithm.

    Examples
    --------
    >>> bench.add_metric(name="best_found", metric=FractionOfOverallBestSolution())
    >>> bench.add_plot(name="avg_best", plot=AverageBestSolutionFoundRatioPlot())
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
                "best_solution_found": metric_result.fraction_of_overall_best_solution,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(
                FractionOfOverallBestSolution
            )
        ]

        self.create(
            rows=rows,
            x="algorithm",
            y="best_solution_found",
            xlabel="Algorithm",
            ylabel="Best Solution Found",
            title="Average best solution found per Solver (1.0 = optimal)",
            hline=1.0,
            hline_label="Optimal (1.0)",
        )
