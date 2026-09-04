"""Built-in plots for benchmarking visualizations."""

from luna_bench.plots.analysis import (
    ApproximationRatioVsParameterPlot,
    ApproximationRatioVsVarNumberPlot,
    FeasibilityRatioVsVarNumberPlot,
    RuntimeVsParameterPlot,
    RuntimeVsVarNumberPlot,
)
from luna_bench.plots.dimensions import (
    PERCENT,
    AlgorithmDimension,
    BaseDimension,
    Dimension,
    FeatureDimension,
    GridDimension,
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
from luna_bench.plots.plot_style import Annotation, ErrorBars, Figure, Missing, OptionBundle, PlotStyle, Theme
from luna_bench.plots.properties import VarNumberBarChartPlot
from luna_bench.plots.summary import plot_summary

__all__ = [
    # The scale every ratio is drawn in
    "PERCENT",
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
    "GridDimension",
    "MetricDimension",
    "Missing",
    "ModelDimension",
    "OptionBundle",
    "ParameterDimension",
    "PlotStyle",
    "RuntimePerModelPlot",
    "RuntimePlot",
    "RuntimeVsParameterPlot",
    "RuntimeVsVarNumberPlot",
    "Theme",
    "TimeToSolutionPlot",
    # Property plots
    "VarNumberBarChartPlot",
    # Summary of every plot of a benchmark
    "plot_summary",
]
