"""Every percent-scaled ratio plot should state its optimum in the unit of its own axis."""

import pytest

from luna_bench.plots import (
    ApproximationRatioPlot,
    ApproximationRatioVsParameterPlot,
    BestSolutionFoundRatioPlot,
    FractionOfOverallBestSolutionPlot,
)
from luna_bench.plots.dimensions import PERCENT


@pytest.mark.parametrize(
    "plot_cls",
    [
        ApproximationRatioPlot,
        ApproximationRatioVsParameterPlot,
        BestSolutionFoundRatioPlot,
        FractionOfOverallBestSolutionPlot,
    ],
)
def test_a_percent_axis_never_states_its_optimum_as_a_ratio(plot_cls: type) -> None:
    """A title saying '1.0 = optimal' over an axis labelled [%] disagrees with itself."""
    plot = plot_cls()

    assert plot.y.scale == PERCENT, "fixture assumes a percent-scaled axis"
    assert "1.0 = optimal" not in plot.figure.title
    assert "100% = optimal" in plot.figure.title
