from abc import ABC

from luna_bench.custom import BasePlot
from luna_bench.helpers.optional_dependencies import check_optional_dependency


class SeabornPlot(BasePlot, ABC):
    """Base of a seaborn-oriented plot with a shared figure and axis configuration.

    Requires
    --------
    Install the 'pre-defined' extra: ``pip install luna-bench[pre-defined]``
    """

    width: int = 8
    height: int = 6
    dpi: int = 100
    show: bool = True

    def setup_figure(self) -> None:
        """Create a matplotlib figure."""
        check_optional_dependency("matplotlib")
        from matplotlib import pyplot as plt  # noqa: PLC0415

        plt.figure(figsize=(self.width, self.height), dpi=self.dpi)

    def finalize_plot(
        self,
        xlabel: str,
        ylabel: str,
        title: str,
        ylim: tuple[float, float] | None = None,
        x_rotation: int = 45,
    ) -> None:
        """Apply common axis labels, title, limits, and display behavior.

        Parameters
        ----------
        xlabel : str
            Label for the x-axis.
        ylabel : str
            Label for the y-axis.
        title : str
            Plot title.
        ylim : tuple[float, float] | None, optional
            Lower and upper y-axis limits, by default ``None``.
        x_rotation : int, optional
            Rotation angle for x-axis tick labels, by default ``45``.
        """
        check_optional_dependency("matplotlib")
        from matplotlib import pyplot as plt  # noqa: PLC0415

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
