from abc import ABC
from logging import Logger
from typing import Any, ClassVar

from luna_quantum import Logging
from matplotlib import pyplot as plt
from pandas import DataFrame
from seaborn import scatterplot

from luna_bench.components.plots.generics.seaborn_plot import SeabornPlot
from luna_bench.components.plots.utils import AqariosColours


class ScatterPlot(SeabornPlot, ABC):
    """Base helper for generating seaborn scatter plots."""

    logger: ClassVar[Logger] = Logging.get_logger(__name__)

    def create(
        self,
        rows: list[dict[str, Any]],
        xlabel: str,
        ylabel: str,
        title: str,
        hue: str,
        x: str = "x",
        y: str = "y",
        hline: float | None = None,
        hline_label: str | None = None,
        hcolor: str = AqariosColours.SUCCESS,
    ) -> None:
        """Create a scatter plot from row-oriented data.

        Parameters
        ----------
        rows : dict[str, Any]
            Row-oriented mapping used to construct the plotting DataFrame.
        xlabel : str
            Label for the x-axis.
        ylabel : str
            Label for the y-axis.
        title : str
            Plot title.
        hue : str
            Column used to color points by group.
        x : str, optional
            Column name mapped to the x-axis, by default ``"x"``.
        y : str, optional
            Column name mapped to the y-axis, by default ``"y"``.
        hline : float | None, optional
            Optional horizontal reference line value, by default ``None``.
        hline_label : str | None, optional
            Legend label for the horizontal reference line, by default ``None``.
        hcolor : str, optional
            Color of the horizontal reference line, by default ``AqariosColours.SUCCESS``.
        """
        if not rows:
            self.logger.warning(f"{self.__class__}: no data to plot")
            return

        df = DataFrame(rows)

        self.setup_figure()
        scatterplot(
            data=df,
            x=x,
            y=y,
            hue=hue,
            palette=AqariosColours.palette(df[hue].nunique()),
            s=60,
            alpha=0.8,
        )

        if hline:
            plt.axhline(y=hline, color=hcolor, linestyle="--", alpha=0.7, label=hline_label)

        self.finalize_plot(
            xlabel=xlabel,
            ylabel=ylabel,
            title=title,
            x_rotation=0,
        )
