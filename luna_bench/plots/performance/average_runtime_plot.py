"""Average runtime per solver bar chart."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from luna_bench.custom import plot
from luna_bench.metrics.runtime import Runtime
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom import BenchmarkResultContainer


@plot(Runtime)
class AverageRuntimePlot(BarPlot):
    """Bar chart of the mean wall-clock runtime each algorithm needed.

    One bar per algorithm, averaged over every model in the benchmark, with the
    spread across those models as the error bar. Lower is better.

    Requires the ``Runtime`` metric.

    Every display option is inherited and can be set when the plot is constructed,
    e.g. ``AverageRuntimePlot(annotate=False, file_formats=("pgf", "png"))``.
    `BarPlot` documents the colours, error bars, value annotations and grouping by a
    feature; `SeabornPlot` the figure size and the output formats.

    Attributes
    ----------
    figure_filename : str
        Stem of the written figure files, by default ``"average_runtime"``.

    Examples
    --------
    >>> bench.add_metric(name="runtime", metric=Runtime())
    >>> bench.add_plot(name="avg_runtime", plot=AverageRuntimePlot())

    See Also
    --------
    RuntimePerModelPlot : The same numbers broken down per model.
    """

    figure_filename: str = "average_runtime"

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
                "runtime_seconds": metric_result.runtime_seconds,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(Runtime)
        ]

        self.create(
            save_dir=save_dir,
            rows=rows,
            x="algorithm",
            y="runtime_seconds",
            title="Average Runtime per Solver",
            xlabel="Algorithm",
            ylabel="Runtime (s)",
            **self.apply_grouping(benchmark_results, rows),
        )
