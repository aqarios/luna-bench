"""Built-in plots for benchmarking visualizations."""

from luna_bench.plots.analysis import (
    ApproximationRatioVsVarNumberPlot,
    FeasibilityRatioVsVarNumberPlot,
    RuntimeVsVarNumberPlot,
)
from luna_bench.plots.performance import (
    AverageApproximationRatioPlot,
    AverageBestSolutionFoundRatioPlot,
    AverageFeasibilityRatioPlot,
    AverageFoBRatioPlot,
    AverageFractionOfOverallBestSolutionPlot,
    AverageRuntimePlot,
    AverageTimeToSolutionPlot,
    FeasibleSolutionFoundPlot,
    RuntimePerModelPlot,
)
from luna_bench.plots.properties import VarNumberBarChartPlot

__all__ = [
    "ApproximationRatioVsVarNumberPlot",
    "AverageApproximationRatioPlot",
    "AverageBestSolutionFoundRatioPlot",
    "AverageFeasibilityRatioPlot",
    "AverageFoBRatioPlot",
    "AverageFractionOfOverallBestSolutionPlot",
    # Performance plots
    "AverageRuntimePlot",
    "AverageTimeToSolutionPlot",
    "FeasibilityRatioVsVarNumberPlot",
    "FeasibleSolutionFoundPlot",
    "RuntimePerModelPlot",
    # Analysis plots
    "RuntimeVsVarNumberPlot",
    # Property plots
    "VarNumberBarChartPlot",
]
