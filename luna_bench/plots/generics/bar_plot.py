import logging
from abc import ABC
from logging import Logger
from typing import Any, ClassVar

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D

from luna_bench.plots.generics.seaborn_plot import SeabornPlot
from luna_bench.plots.utils import AqariosColours
from luna_bench.plots.utils.aggregation_enum import Aggregation


class BarPlot(SeabornPlot, ABC):
    """Base helper for generating aggregated seaborn bar plots."""

    logger: ClassVar[Logger] = logging.getLogger(__name__)

    color: str = AqariosColours.AQARIOS

    def create(  # noqa: PLR0913 # There are no good alternatives to just have all parameters listed here.
        self,
        *,
        rows: list[dict[str, Any]],
        xlabel: str,
        ylabel: str,
        title: str,
        x: str = "x",
        y: str = "y",
        aggregation: Aggregation = Aggregation.MEAN,
        hue: str | None = None,
        hline: float | None = None,
        hline_label: str | None = None,
        ylim: tuple[float, float] | None = None,
        legend: bool = False,
    ) -> None:
        """Create a bar plot from row-oriented data.

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
        x : str, optional
            Column name mapped to the x-axis, by default ``"x"``.
        y : str, optional
            Column name mapped to the y-axis, by default ``"y"``.
        aggregation : Aggregation, optional
            Aggregation strategy applied by seaborn, by default ``Aggregation.MEAN``.
        hue : str | None, optional
            Optional grouping column for grouped bars, by default ``None``.
        hline : float | None, optional
            Optional horizontal reference line value, by default ``None``.
        hline_label : str | None, optional
            Legend label for the horizontal reference line, by default ``None``.
        ylim : tuple[float, float] | None, optional
            Lower and upper y-axis limits, by default ``None``.
        legend : bool, optional
            Whether seaborn should create a legend for hue groups, by default ``False``.
        """
        if not rows:
            self.logger.warning(f"{self.__class__}: no data to plot")
            return

        df = pd.DataFrame(rows)

        self.setup_figure()

        sns.barplot(
            data=df,
            x=x,
            y=y,
            hue=hue,
            estimator=aggregation.value,
            errorbar=aggregation.errorbar,
            color=self.color if hue is None else None,
            palette=AqariosColours.palette(df[hue].nunique()) if hue else None,
            legend=legend,
        )

        if hline is not None:
            plt.axhline(y=hline, color=AqariosColours.SUCCESS, linestyle="--", alpha=0.7, label=hline_label)

        handles, labels = plt.gca().get_legend_handles_labels()
        err_handle = Line2D([], [], color="black", marker="|", markersize=8, linestyle="none", label="± 1 SD")
        handles.append(err_handle)
        labels.append("± 1 SD")

        if handles:
            plt.legend(handles=handles, labels=labels)

        self.finalize_plot(xlabel, ylabel, title, ylim)
