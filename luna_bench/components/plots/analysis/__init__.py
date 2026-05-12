"""Performance analysis plots showing solver metrics vs model properties."""

from .approximation_ratio_vs_var_number_plot import ApproximationRatioVsVarNumberPlot
from .feasibility_ratio_vs_var_number_plot import FeasibilityRatioVsVarNumberPlot
from .runtime_vs_var_number_plot import RuntimeVsVarNumberPlot

__all__ = [
    "ApproximationRatioVsVarNumberPlot",
    "FeasibilityRatioVsVarNumberPlot",
    "RuntimeVsVarNumberPlot",
]
