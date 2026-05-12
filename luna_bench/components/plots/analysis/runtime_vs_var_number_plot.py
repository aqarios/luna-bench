"""Feature vs metric scatter plots using the new BenchmarkResults interface.

Shows scatter plots combining features (x-axis) with metrics (y-axis),
colour-coded by algorithm.
"""

from __future__ import annotations

from luna_bench.base_components.data_types.benchmark_results import BenchmarkResults
from luna_bench.components.features.var_num_feature import VarNumberFeature
from luna_bench.components.metrics.runtime import Runtime
from luna_bench.components.plots.generics.scatter_plot import ScatterPlot
from luna_bench.helpers.decorators import plot


@plot([VarNumberFeature, Runtime])
class RuntimeVsVarNumberPlot(ScatterPlot):
    """Scatter plot showing runtime vs number of variables per model/algorithm.

    Examples
    --------
    >>> bench.add_feature(name="var_count", feature=VarNumberFeature())
    >>> bench.add_metric(name="runtime", metric=Runtime())
    >>> bench.add_plot(name="runtime_vs_vars", plot=RuntimeVsVarNumberPlot())
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
                "var_number": benchmark_results.features[model_name].first(VarNumberFeature).var_number,
                "runtime_seconds": metric_result.runtime_seconds,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(Runtime)
        ]

        self.create(
            rows=rows,
            x="var_number",
            y="runtime_seconds",
            xlabel="Number of Variables",
            ylabel="Runtime (s)",
            title="Runtime vs Model Size",
            hue="algorithm",
        )
