"""Bar chart showing the number of variables per model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench.custom import plot
from luna_bench.features.var_num_feature import VarNumberFeature
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer


@plot(VarNumberFeature)
class VarNumberBarChartPlot(BarPlot):
    """Bar chart showing the number of variables per model.

    Examples
    --------
    >>> bench.add_feature(name="var_count", feature=VarNumberFeature())
    >>> bench.add_plot(name="var_number", plot=VarNumberBarChartPlot())
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
                "var_number": benchmark_results.features[model_name].first(VarNumberFeature).var_number,
            }
            for model_name, feature_results in benchmark_results.features.items()
        ]

        self.create(
            rows=rows,
            x="model",
            y="var_number",
            xlabel="Model",
            ylabel="Number of Variables",
            title="Variables per Model",
        )
