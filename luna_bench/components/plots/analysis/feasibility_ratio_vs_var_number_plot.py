"""Feasibility ratio vs number of variables scatter plot."""

from __future__ import annotations

from luna_bench.base_components.data_types.benchmark_results import BenchmarkResults
from luna_bench.components.features.var_num_feature import VarNumberFeature
from luna_bench.components.metrics.feasbility_ratio import FeasibilityRatio
from luna_bench.components.plots.generics.scatter_plot import ScatterPlot
from luna_bench.helpers.decorators import plot


@plot(required_features=VarNumberFeature, required_metrics=FeasibilityRatio)
class FeasibilityRatioVsVarNumberPlot(ScatterPlot):
    """Scatter plot showing feasibility ratio vs number of variables per model/algorithm.

    Examples
    --------
    >>> bench.add_feature(name="var_count", feature=VarNumberFeature())
    >>> bench.add_metric(name="feasibility", metric=FeasibilityRatio())
    >>> bench.add_plot(name="feasibility_vs_vars", plot=FeasibilityRatioVsVarNumberPlot())
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
                "feasibility_ratio": metric_result.feasibility_ratio,
            }
            for model_name, algorithm_name, metric_result in benchmark_results.get_all_metrics_of_type(FeasibilityRatio)
        ]
        self.create(
            rows=rows,
            xlabel="Number of Variables",
            ylabel="Feasibility Ratio",
            title="Feasibility Ratio vs Model Size",
            hue="algorithm",
            hline=1.0,
            hline_label="Upper Limit (1.0)",
        )
