"""Average runtime per solver bar chart."""

from __future__ import annotations

from luna_bench.base_components.data_types.benchmark_results import BenchmarkResults
from luna_bench.components.metrics.runtime import Runtime
from luna_bench.components.plots.generics.bar_plot import BarPlot
from luna_bench.helpers.decorators import plot


@plot(required_metrics=Runtime)
class AverageRuntimePlot(BarPlot):
    """Bar chart showing average runtime per algorithm.

    Examples
    --------
    >>> bench.add_metric(name="runtime", metric=Runtime())
    >>> bench.add_plot(name="avg_runtime", plot=AverageRuntimePlot())
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
                "runtime_seconds": metric_result.runtime_seconds,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(Runtime)
        ]

        self.create(
            rows=rows,
            x="algorithm",
            y="runtime_seconds",
            title="Average Runtime per Solver",
            xlabel="Algorithm",
            ylabel="Runtime (s)",
        )
