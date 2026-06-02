"""Shared seaborn-oriented plot infrastructure with figure, axis, and save support."""

from __future__ import annotations

from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from luna_quantum import Logging

from luna_bench.custom import BasePlot
from luna_bench.helpers.optional_dependencies import check_optional_dependency

if TYPE_CHECKING:
    from logging import Logger


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

    figure_filename: str = "seaborn_plot.png"

    logger: ClassVar[Logger] = Logging.get_logger(__name__)

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
        save_dir: str | None = None,
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

        # Try duck-typed save_dir attribute first (set by OutputUc at runtime),
        # then fall back to the explicit parameter.
        effective_save_dir = save_dir or getattr(self, "save_dir", None)
        if effective_save_dir:
            save_path = Path(effective_save_dir) / self.figure_filename
            save_path.parent.mkdir(parents=True, exist_ok=True)
            plt.savefig(str(save_path), dpi=self.dpi, bbox_inches="tight")

            self.logger.info("Saved figure to %s", save_path)

        if self.show:
            plt.show()
