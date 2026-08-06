"""Share of models for which an algorithm found at least one feasible solution."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from luna_bench.custom import plot
from luna_bench.metrics import FeasibilityRatio
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom import BenchmarkResultContainer

PERCENT = 100.0


@plot(FeasibilityRatio)
class FeasibleSolutionFoundPlot(BarPlot):
    """Bar chart showing the percentage of models solved feasibly per algorithm.

    A model counts as solved when at least one sample was feasible, i.e. when the
    ``FeasibilityRatio`` is greater than zero. Averaging that indicator over all
    models gives the share of the benchmark an algorithm could handle at all,
    independent of how many of its samples were feasible.

    Every display option is inherited and can be set when the plot is constructed,
    e.g. ``FeasibleSolutionFoundPlot(annotate=False, file_formats=("pgf", "png"))``.
    `BarPlot` documents the colours, error bars, value annotations and grouping by a
    feature; `SeabornPlot` the figure size and the output formats.

    Attributes
    ----------
    figure_filename : str
        Stem of the written figure files, by default ``"feasible_solution_found"``.
    annotate_format : str
        Format of the value written above each bar, by default ``"{:.1f}%"``.

    Examples
    --------
    >>> bench.add_metric(name="feasibility", metric=FeasibilityRatio())
    >>> bench.add_plot(name="feasible_found", plot=FeasibleSolutionFoundPlot())
    """

    figure_filename: str = "feasible_solution_found"
    annotate_format: str = "{:.1f}%"

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
                "feasible_found": PERCENT if metric_result.feasibility_ratio > 0 else 0.0,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(FeasibilityRatio)
        ]

        self.create(
            save_dir=save_dir,
            rows=rows,
            x="algorithm",
            y="feasible_found",
            xlabel="Algorithm",
            ylabel="Feasible solution found [% of models]",
            title="Models with a Feasible Solution per Algorithm",
            ylim=(0, 105),
            **self.apply_grouping(benchmark_results, rows),
        )
