from abc import ABC
from typing import Any

from matplotlib import pyplot as plt
from pandas import DataFrame
from seaborn import scatterplot

from luna_bench.components.plots.generics.seaborn_plot import SeabornPlot
from luna_bench.components.plots.utils import AqariosColours


class ScatterPlot(SeabornPlot, ABC):
    def create(
        self,
        rows: dict[str, Any],
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

        if not rows:
            self.logger.warning(f"{self.__name__}: no data to plot")
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
