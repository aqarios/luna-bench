from __future__ import annotations

from luna_bench.base_components.data_types.benchmark_results import BenchmarkResults
from luna_bench.components.features.var_num_feature import VarNumberFeature
from luna_bench.components.metrics.approximation_ratio import ApproximationRatio
from luna_bench.components.plots.generics.scatter_plot import ScatterPlot
from luna_bench.helpers.decorators import plot


@plot([VarNumberFeature, ApproximationRatio])
class ApproximationRatioVsVarNumberPlot(ScatterPlot):
    """Scatter plot showing an approximation ratio vs. number of variables per model/algorithm.

    Examples
    --------
    >>> bench.add_feature(name="var_count", feature=VarNumberFeature())
    >>> bench.add_metric(name="approx_ratio", metric=ApproximationRatio())
    >>> bench.add_plot(name="approx_vs_vars", plot=ApproximationRatioVsVarNumberPlot())
    """

    def run(self, benchmark_results: BenchmarkResults) -> None:
        """Generate plot output from benchmark results.

        Parameters
        ----------
        benchmark_results : BenchmarkResults
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
            rows=rows,
            xlabel="Number of Variables",
            ylabel="Approximation Ratio",
            title="Approximation Ratio vs Number of Variables",
            hue="algorithm",
            hline=1.0,
            hline_label="Optimal (1.0)",
        )
