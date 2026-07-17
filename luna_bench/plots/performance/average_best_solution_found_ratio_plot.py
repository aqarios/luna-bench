"""Average time to solution per solver bar chart."""

from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench.custom import plot
from luna_bench.metrics import BestSolutionFoundRatio
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom import BenchmarkResultContainer


@plot(BestSolutionFoundRatio)
class AverageBestSolutionFoundRatioPlot(BarPlot):
    """Bar chart showing average time to solution per algorithm.

    Examples
    --------
    >>> bench.add_metric(name="time_to_solution", metric=BestSolutionFoundRatio())
    >>> bench.add_plot(name="avg_bsfr", plot=AverageBestSolutionFoundRatioPlot())
    """

    figure_filename: str = "average_best_solution_found_ratio"

    def run(self, benchmark_results: BenchmarkResultContainer, save_dir: str | None = None) -> None:
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
                "time_to_solution": metric_result.best_solution_found,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(
                BestSolutionFoundRatio
            )
        ]

        self.create(
            save_dir=save_dir,
            rows=rows,
            x="algorithm",
            y="time_to_solution",
            xlabel="Algorithm",
            ylabel="Best Solution Found Ratio",
            title="Average Time to Solution per Algorithm (higher is better)",
        )
