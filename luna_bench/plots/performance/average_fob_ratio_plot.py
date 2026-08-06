"""Average fraction of overall best solution per solver bar chart."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from luna_bench.custom import plot
from luna_bench.metrics import FractionOfOverallBestSolution
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom import BenchmarkResultContainer


@plot(FractionOfOverallBestSolution)
class AverageFoBRatioPlot(BarPlot):
    """Bar chart of the mean fraction of the overall best solution per algorithm.

    Same metric as `AverageFractionOfOverallBestSolutionPlot`, written to its own file
    under the ``fraction_of_overall_best`` column name.

    Requires the ``FractionOfOverallBestSolution`` metric.

    Every display option is inherited and can be set when the plot is constructed,
    e.g. ``AverageFoBRatioPlot(annotate=False, file_formats=("pgf", "png"))``.
    `BarPlot` documents the colours, error bars, value annotations and grouping by a
    feature; `SeabornPlot` the figure size and the output formats.

    Attributes
    ----------
    figure_filename : str
        Stem of the written figure files, by default ``"average_fob_ratio"``.

    Examples
    --------
    >>> bench.add_metric(name="fob", metric=FractionOfOverallBestSolution())
    >>> bench.add_plot(name="avg_fob", plot=AverageFoBRatioPlot())
    """

    figure_filename: str = "average_fob_ratio"

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
                "fraction_of_overall_best": metric_result.fraction_of_overall_best_solution,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(
                FractionOfOverallBestSolution
            )
        ]

        self.create(
            save_dir=save_dir,
            rows=rows,
            x="algorithm",
            y="fraction_of_overall_best",
            xlabel="Algorithm",
            ylabel="Fraction of overall best solution",
            title="Average Fraction of overall best Ratio per Solver (1.0 = optimal)",
            hline=1.0,
            hline_label="Optimal (1.0)",
            **self.apply_grouping(benchmark_results, rows),
        )
