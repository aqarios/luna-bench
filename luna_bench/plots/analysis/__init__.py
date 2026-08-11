"""Performance analysis plots showing solver metrics vs model properties."""

from .approximation_ratio_vs_var_number_plot import ApproximationRatioVsVarNumberPlot
from .feasibility_ratio_vs_var_number_plot import FeasibilityRatioVsVarNumberPlot
from .metric_vs_parameter_plot import ApproximationRatioVsParameterPlot, RuntimeVsParameterPlot
from .runtime_vs_var_number_plot import RuntimeVsVarNumberPlot

__all__ = [
    "ApproximationRatioVsParameterPlot",
    "ApproximationRatioVsVarNumberPlot",
    "FeasibilityRatioVsVarNumberPlot",
    "RuntimeVsParameterPlot",
    "RuntimeVsVarNumberPlot",
]
