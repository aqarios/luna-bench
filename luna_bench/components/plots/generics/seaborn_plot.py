from abc import ABC

from matplotlib import pyplot as plt

from luna_bench.base_components import BasePlot


class SeabornPlot(BasePlot, ABC):
    width: int = 8
    height: int = 6
    dpi: int = 100
    show: bool = True

    def setup_figure(self) -> None:
        plt.figure(width=self.width, height=self.height, dpi=dpi)

    def finalize_plot(
        self,
        xlabel: str,
        ylabel: str,
        title: str,
        ylim: tuple[float, float] | None = None,
        x_rotation: int = 45,
    ) -> None:

        if x_rotation > 0:
            plt.xticks(rotation=x_rotation, ha="right")

        if ylabel:
            plt.ylabel(ylabel)

        if xlabel:
            plt.xlabel(xlabel)

        if title:
            plt.title(title)

        if ylim is not None:
            plt.ylim(*ylim)

        plt.tight_layout()

        if self.show:
            plt.show()
