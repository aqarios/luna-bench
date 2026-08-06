"""Average best-solution-found ratio per solver bar chart."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from luna_bench.custom import plot
from luna_bench.metrics import BestSolutionFoundRatio
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom import BenchmarkResultContainer


@plot(BestSolutionFoundRatio)
class AverageBestSolutionFoundRatioPlot(BarPlot):
    """Bar chart of the mean best-solution-found ratio per algorithm.

    The share of samples that reached the best solution, averaged over every model,
    with the spread across those models as the error bar. Higher is better.

    Requires the ``BestSolutionFoundRatio`` metric.

    Every display option is inherited and can be set when the plot is constructed,
    e.g. ``AverageBestSolutionFoundRatioPlot(annotate=False, file_formats=("pgf", "png"))``.
    `BarPlot` documents the colours, error bars, value annotations and grouping by a
    feature; `SeabornPlot` the figure size and the output formats.

    Attributes
    ----------
    figure_filename : str
        Stem of the written figure files, by default ``"average_best_solution_found_ratio"``.

    Examples
    --------
    >>> bench.add_metric(name="bsf_ratio", metric=BestSolutionFoundRatio())
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
        rows: list[dict[str, Any]] = [
            {
                "algorithm": algorithm_name,
                "model": model_name,
                "best_solution_found_ratio": metric_result.best_solution_found,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(
                BestSolutionFoundRatio
            )
        ]

        self.create(
            save_dir=save_dir,
            rows=rows,
            x="algorithm",
            y="best_solution_found_ratio",
            xlabel="Algorithm",
            ylabel="Best Solution Found Ratio",
            title="Average Best Solution Found Ratio per Algorithm (higher is better)",
            **self.apply_grouping(benchmark_results, rows),
        )
