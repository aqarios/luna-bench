"""Average approximation ratio per solver bar chart."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from luna_bench.custom import plot
from luna_bench.metrics import ApproximationRatio
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom import BenchmarkResultContainer


@plot(ApproximationRatio)
class AverageApproximationRatioPlot(BarPlot):
    """Bar chart of the mean approximation ratio per algorithm.

    The approximation ratio compares an algorithm's objective value against the known
    optimum, so ``1.0`` - marked by the reference line - means the optimum was reached.
    One bar per algorithm, averaged over every model, with the spread across those
    models as the error bar.

    Requires the ``ApproximationRatio`` metric.

    Every display option is inherited and can be set when the plot is constructed,
    e.g. ``AverageApproximationRatioPlot(annotate=False, file_formats=("pgf", "png"))``.
    `BarPlot` documents the colours, error bars, value annotations and grouping by a
    feature; `SeabornPlot` the figure size and the output formats.

    Attributes
    ----------
    figure_filename : str
        Stem of the written figure files, by default ``"average_approximation_ratio"``.

    Examples
    --------
    >>> bench.add_metric(name="approx_ratio", metric=ApproximationRatio())
    >>> bench.add_plot(name="avg_approx", plot=AverageApproximationRatioPlot())

    See Also
    --------
    ApproximationRatioVsVarNumberPlot : The same ratio against model size.
    """

    figure_filename: str = "average_approximation_ratio"

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
                "approximation_ratio": metric_result.approximation_ratio,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(
                ApproximationRatio
            )
        ]

        self.create(
            save_dir=save_dir,
            rows=rows,
            x="algorithm",
            y="approximation_ratio",
            xlabel="Algorithm",
            ylabel="Approximation Ratio",
            title="Average Approximation Ratio per Solver (1.0 = optimal)",
            hline=1.0,
            hline_label="Optimal (1.0)",
            **self.apply_grouping(benchmark_results, rows),
        )
