"""Bar chart showing the number of variables per model."""

from __future__ import annotations

from luna_bench.base_components.data_types.benchmark_results import BenchmarkResults
from luna_bench.components.features.var_num_feature import VarNumberFeature
from luna_bench.components.plots.generics.bar_plot import BarPlot
from luna_bench.helpers.decorators import plot


@plot(required_features=VarNumberFeature)
class VarNumberBarChartPlot(BarPlot):
    """Bar chart showing the number of variables per model.

    Examples
    --------
    >>> bench.add_feature(name="var_count", feature=VarNumberFeature())
    >>> bench.add_plot(name="var_number", plot=VarNumberBarChartPlot())
    """

    def run(self, benchmark_results: BenchmarkResults) -> None:
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
