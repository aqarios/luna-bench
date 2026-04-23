"""Built-in plots for benchmarking visualizations."""

from luna_bench.components.plots.analysis import (
    ApproximationRatioVsVarNumberPlot,
    FeasibilityRatioVsVarNumberPlot,
    RuntimeVsVarNumberPlot,
)
from luna_bench.components.plots.performance import (
    AverageApproximationRatioPlot,
    AverageBestSolutionFoundRatioPlot,
    AverageFeasibilityRatioPlot,
    AverageFoBRatioPlot,
    AverageRuntimePlot,
    RuntimePerModelPlot,
)
from luna_bench.components.plots.properties import VarNumberBarChartPlot

__all__ = [
    "ApproximationRatioVsVarNumberPlot",
    "AverageApproximationRatioPlot",
    "AverageBestSolutionFoundRatioPlot",
    "AverageFeasibilityRatioPlot",
    "AverageFoBRatioPlot",
    # Performance plots
    "AverageRuntimePlot",
    "FeasibilityRatioVsVarNumberPlot",
    "RuntimePerModelPlot",
    # Analysis plots
    "RuntimeVsVarNumberPlot",
    # Property plots
    "VarNumberBarChartPlot",
]
