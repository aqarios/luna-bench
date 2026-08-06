"""Average best solution found per solver bar chart."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from luna_bench.custom import plot
from luna_bench.metrics.fraction_of_overall_best_solution import FractionOfOverallBestSolution
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom import BenchmarkResultContainer


@plot(FractionOfOverallBestSolution)
class AverageFractionOfOverallBestSolutionPlot(BarPlot):
    """Bar chart of the mean fraction of the overall best solution per algorithm.

    Each algorithm's objective value is measured against the best value *any*
    algorithm in the benchmark reached for that model, so ``1.0`` - marked by the
    reference line - means it was the best of the field. Useful when no optimum is
    known. Averaged over every model, with the spread across models as the error bar.

    Requires the ``FractionOfOverallBestSolution`` metric.

    Every display option is inherited and can be set when the plot is constructed,
    e.g. ``AverageFractionOfOverallBestSolutionPlot(annotate=False, file_formats=("pgf", "png"))``.
    `BarPlot` documents the colours, error bars, value annotations and grouping by a
    feature; `SeabornPlot` the figure size and the output formats.

    Attributes
    ----------
    figure_filename : str
        Stem of the written figure files, by default ``"average_fraction_of_overall_best_solution"``.

    Examples
    --------
    >>> bench.add_metric(name="best_found", metric=FractionOfOverallBestSolution())
    >>> bench.add_plot(name="avg_best", plot=AverageFractionOfOverallBestSolutionPlot())
    """

    figure_filename: str = "average_fraction_of_overall_best_solution"

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
                "best_solution_found": metric_result.fraction_of_overall_best_solution,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(
                FractionOfOverallBestSolution
            )
        ]

        self.create(
            save_dir=save_dir,
            rows=rows,
            x="algorithm",
            y="best_solution_found",
            xlabel="Algorithm",
            ylabel="Best Solution Found",
            title="Average best solution found per Solver (1.0 = optimal)",
            hline=1.0,
            hline_label="Optimal (1.0)",
            **self.apply_grouping(benchmark_results, rows),
        )
