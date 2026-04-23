import logging
from abc import ABC
from logging import Logger
from typing import Any, ClassVar

import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt
from matplotlib.lines import Line2D

from luna_bench.components.plots.generics.seaborn_plot import SeabornPlot
from luna_bench.components.plots.utils import AqariosColours
from luna_bench.components.plots.utils.aggregation_enum import Aggregation


class BarPlot(SeabornPlot, ABC):
    logger: ClassVar[Logger] = logging.getLogger(__name__)

    color: str = AqariosColours.AQARIOS

    def create(
        self,
        rows: dict[str, Any],
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

        if not rows:
            self.logger.warning(f"{self.__name__}: no data to plot")
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
