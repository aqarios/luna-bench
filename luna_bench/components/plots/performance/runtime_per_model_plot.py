"""Runtime per model grouped by algorithm."""

from __future__ import annotations

from luna_bench.base_components.data_types.benchmark_results import BenchmarkResults
from luna_bench.components.metrics.runtime import Runtime
from luna_bench.components.plots.generics.bar_plot import BarPlot
from luna_bench.helpers.decorators import plot


@plot(required_metrics=Runtime)
class RuntimePerModelPlot(BarPlot):
    """Bar chart showing runtime per model grouped by algorithm.

    Examples
    --------
    >>> bench.add_metric(name="runtime", metric=Runtime())
    >>> bench.add_plot(name="runtime_per_model", plot=RuntimePerModelPlot())
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
                "model": model_name,
                "algorithm": algorithm_name,
                "runtime_seconds": metric_result.runtime_seconds,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(Runtime)
        ]

        self.create(
            rows=rows,
            x="model",
            y="runtime_seconds",
            hue="algorithm",
            xlabel="Model",
            ylabel="Runtime (s)",
            title="Runtime per Model by Algorithm",
            legend=True,
        )
