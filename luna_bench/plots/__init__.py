"""Built-in plots for benchmarking visualizations."""

from luna_bench.plots.analysis import (
    ApproximationRatioVsParameterPlot,
    ApproximationRatioVsVarNumberPlot,
    FeasibilityRatioVsVarNumberPlot,
    RuntimeVsParameterPlot,
    RuntimeVsVarNumberPlot,
)
from luna_bench.plots.dimensions import (
    AlgorithmDimension,
    BaseDimension,
    Dimension,
    FeatureDimension,
    MetricDimension,
    ModelDimension,
    ParameterDimension,
)
from luna_bench.plots.performance import (
    ApproximationRatioPlot,
    BestSolutionFoundRatioPlot,
    FeasibilityRatioPlot,
    FeasibleSampleRatioPlot,
    FeasibleSolutionFoundPlot,
    FractionOfOverallBestSolutionPlot,
    RuntimePerModelPlot,
    RuntimePlot,
    TimeToSolutionPlot,
)
from luna_bench.plots.plot_style import Annotation, ErrorBars, Figure, OptionBundle, PlotStyle
from luna_bench.plots.properties import VarNumberBarChartPlot
from luna_bench.plots.summary import plot_summary

__all__ = [
    # What a plot organises its data by
    "AlgorithmDimension",
    # Bundles of plot options
    "Annotation",
    # Performance plots
    "ApproximationRatioPlot",
    # Analysis plots
    "ApproximationRatioVsParameterPlot",
    "ApproximationRatioVsVarNumberPlot",
    "BaseDimension",
    "BestSolutionFoundRatioPlot",
    "Dimension",
    "ErrorBars",
    "FeasibilityRatioPlot",
    "FeasibilityRatioVsVarNumberPlot",
    "FeasibleSampleRatioPlot",
    "FeasibleSolutionFoundPlot",
    "FeatureDimension",
    "Figure",
    "FractionOfOverallBestSolutionPlot",
    "MetricDimension",
    "ModelDimension",
    "OptionBundle",
    "ParameterDimension",
    "PlotStyle",
    "RuntimePerModelPlot",
    "RuntimePlot",
    "RuntimeVsParameterPlot",
    "RuntimeVsVarNumberPlot",
    "TimeToSolutionPlot",
    # Property plots
    "VarNumberBarChartPlot",
    # Summary of every plot of a benchmark
    "plot_summary",
]
