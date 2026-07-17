"""Average time to solution per solver bar chart."""

from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench.custom import plot
from luna_bench.metrics import TimeToSolution
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom import BenchmarkResultContainer


@plot(TimeToSolution)
class AverageTimeToSolutionPlot(BarPlot):
    """Bar chart showing average time to solution per algorithm.

    Examples
    --------
    >>> bench.add_metric(name="time_to_solution", metric=TimeToSolution())
    >>> bench.add_plot(name="avg_tts", plot=AverageTimeToSolutionPlot())
    """

    figure_filename: str = "average_time_to_solution"

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
                "time_to_solution": metric_result.time_to_solution,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(TimeToSolution)
        ]

        self.create(
            save_dir=save_dir,
            rows=rows,
            x="algorithm",
            y="time_to_solution",
            xlabel="Algorithm",
            ylabel="Time to Solution (TTS)",
            title="Average Time to Solution per Algorithm (lower is better)",
        )
