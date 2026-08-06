"""Runtime per model grouped by algorithm."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from luna_bench.custom import plot
from luna_bench.metrics import Runtime
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom import BenchmarkResultContainer


@plot(Runtime)
class RuntimePerModelPlot(BarPlot):
    """Bar chart of runtime per model, with one bar per algorithm inside each model.

    Keeps the models apart instead of averaging over them, which shows where a
    single hard instance drives an algorithm's average runtime up.

    Requires the ``Runtime`` metric.

    Every display option is inherited and can be set when the plot is constructed,
    e.g. ``RuntimePerModelPlot(annotate=False, file_formats=("pgf", "png"))``.
    `BarPlot` documents the colours, error bars and value annotations; `SeabornPlot` the
    figure size and the output formats. ``group_by`` does not apply here - this plot
    already uses the hue channel for the algorithm.

    Attributes
    ----------
    figure_filename : str
        Stem of the written figure files, by default ``"runtime_per_model"``.

    Examples
    --------
    >>> bench.add_metric(name="runtime", metric=Runtime())
    >>> bench.add_plot(name="runtime_per_model", plot=RuntimePerModelPlot())

    See Also
    --------
    AverageRuntimePlot : The same numbers averaged over all models.
    """

    figure_filename: str = "runtime_per_model"

    def run(self, benchmark_results: BenchmarkResultContainer, save_dir: str | None = None) -> None:
        """Generate plot output from benchmark results.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Aggregated benchmark data consumed by the plot implementation.
        """
        rows: list[dict[str, Any]] = [
            {
                "model": model_name,
                "algorithm": algorithm_name,
                "runtime_seconds": metric_result.runtime_seconds,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(Runtime)
        ]

        self.create(
            save_dir=save_dir,
            rows=rows,
            x="model",
            y="runtime_seconds",
            hue="algorithm",
            xlabel="Model",
            ylabel="Runtime (s)",
            title="Runtime per Model by Algorithm",
            legend=True,
        )
