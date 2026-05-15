"""Average runtime per solver bar chart."""

from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench.custom import plot
from luna_bench.metrics.runtime import Runtime
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer


@plot(Runtime)
class AverageRuntimePlot(BarPlot):
    """Bar chart showing average runtime per algorithm.

    Examples
    --------
    >>> bench.add_metric(name="runtime", metric=Runtime())
    >>> bench.add_plot(name="avg_runtime", plot=AverageRuntimePlot())
    """

    def run(self, benchmark_results: BenchmarkResultContainer) -> None:
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
