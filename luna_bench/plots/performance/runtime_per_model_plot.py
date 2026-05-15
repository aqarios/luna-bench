"""Runtime per model grouped by algorithm."""

from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench.custom import plot
from luna_bench.metrics.runtime import Runtime
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer


@plot(Runtime)
class RuntimePerModelPlot(BarPlot):
    """Bar chart showing runtime per model grouped by algorithm.

    Examples
    --------
    >>> bench.add_metric(name="runtime", metric=Runtime())
    >>> bench.add_plot(name="runtime_per_model", plot=RuntimePerModelPlot())
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
