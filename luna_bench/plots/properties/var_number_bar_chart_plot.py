"""Bar chart showing the number of variables per model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from luna_bench.custom import plot
from luna_bench.features import VarNumberFeature
from luna_bench.plots.generics.bar_plot import BarPlot

if TYPE_CHECKING:
    from luna_bench.custom import BenchmarkResultContainer


@plot(VarNumberFeature)
class VarNumberBarChartPlot(BarPlot):
    """Bar chart showing the number of variables per model.

    Examples
    --------
    >>> bench.add_feature(name="var_count", feature=VarNumberFeature())
    >>> bench.add_plot(name="var_number", plot=VarNumberBarChartPlot())
    """

    figure_filename: str = "var_number_bar_chart"

    def run(self, benchmark_results: BenchmarkResultContainer, save_dir: str | None = None) -> None:
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
            save_dir=save_dir,
            rows=rows,
            x="model",
            y="var_number",
            xlabel="Model",
            ylabel="Number of Variables",
            title="Variables per Model",
        )
