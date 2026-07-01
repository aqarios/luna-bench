from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench.custom import plot
from luna_bench.features import VarNumberFeature
from luna_bench.metrics import ApproximationRatio
from luna_bench.plots.generics.scatter_plot import ScatterPlot

if TYPE_CHECKING:
    from luna_bench.custom import BenchmarkResultContainer


@plot([VarNumberFeature, ApproximationRatio])
class ApproximationRatioVsVarNumberPlot(ScatterPlot):
    """Scatter plot showing an approximation ratio vs. number of variables per model/algorithm.

    Examples
    --------
    >>> bench.add_feature(name="var_count", feature=VarNumberFeature())
    >>> bench.add_metric(name="approx_ratio", metric=ApproximationRatio())
    >>> bench.add_plot(name="approx_vs_vars", plot=ApproximationRatioVsVarNumberPlot())
    """

    figure_filename: str = "approximation_ratio_vs_var_number"

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
                "x": benchmark_results.features[model_name].first(VarNumberFeature).var_number,
                "y": metric_result.approximation_ratio,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(
                ApproximationRatio
            )
        ]
        self.create(
            save_dir=save_dir,
            rows=rows,
            xlabel="Number of Variables",
            ylabel="Approximation Ratio",
            title="Approximation Ratio vs Number of Variables",
            hue="algorithm",
            hline=1.0,
            hline_label="Optimal (1.0)",
        )
