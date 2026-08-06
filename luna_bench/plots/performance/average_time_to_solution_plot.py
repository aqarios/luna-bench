"""Average time to solution per solver bar chart."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from luna_bench.custom import plot
from luna_bench.metrics import TimeToSolution
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom import BenchmarkResultContainer


@plot(TimeToSolution)
class AverageTimeToSolutionPlot(BarPlot):
    """Bar chart of the mean time to solution (TTS) per algorithm.

    TTS is the runtime an algorithm needs to reach its target solution with a given
    confidence, so it weighs speed against success rate. One bar per algorithm,
    averaged over every model, with the spread across those models as the error bar.
    Lower is better.

    Requires the ``TimeToSolution`` metric.

    Every display option is inherited and can be set when the plot is constructed,
    e.g. ``AverageTimeToSolutionPlot(annotate=False, file_formats=("pgf", "png"))``.
    `BarPlot` documents the colours, error bars, value annotations and grouping by a
    feature; `SeabornPlot` the figure size and the output formats.

    Attributes
    ----------
    figure_filename : str
        Stem of the written figure files, by default ``"average_time_to_solution"``.

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
        rows: list[dict[str, Any]] = [
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
            **self.apply_grouping(benchmark_results, rows),
        )
