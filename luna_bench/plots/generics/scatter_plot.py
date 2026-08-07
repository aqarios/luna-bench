from abc import ABC
from logging import Logger
from typing import Any, ClassVar

from pandas import DataFrame

from luna_bench.helpers.optional_dependencies import check_optional_dependency
from luna_bench.logging import BenchLogger
from luna_bench.plots.utils import REFERENCE_LINE_COLOUR, LunaColours

from .seaborn_plot import SeabornPlot


class ScatterPlot(SeabornPlot, ABC):
    """Base helper for generating seaborn scatter plots.

    Requires
    --------
    Install the 'pre-defined' extra: ``pip install luna-bench[pre-defined]``
    """

    logger: ClassVar[Logger] = BenchLogger.get_logger(__name__)

    def create(  # noqa: PLR0913 # There are no good alternatives to just have all parameters listed here.
        self,
        *,
        rows: list[dict[str, Any]],
        xlabel: str,
        ylabel: str,
        title: str,
        hue: str,
        x: str = "x",
        y: str = "y",
        hline: float | None = None,
        hline_label: str | None = None,
        hcolor: str = REFERENCE_LINE_COLOUR,
        save_dir: str | None = None,
        **kwargs: Any,
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
            Color of the horizontal reference line, by default black.
        save_dir : str | None, optional
            Directory to save the figure into, by default ``None``.
        **kwargs : Any
            Additional keyword arguments forwarded to :func:`seaborn.scatterplot`.
            They override the defaults computed here, so anything seaborn understands
            (``palette``, ``style``, ``size``, ``markers``, ...) can be tuned from the
            call site.
        """
        check_optional_dependency("matplotlib")
        check_optional_dependency("seaborn")
        from matplotlib import pyplot as plt  # noqa: PLC0415
        from seaborn import scatterplot  # noqa: PLC0415

        if not rows:
            self.logger.warning(f"{self.__class__}: no data to plot")
            return

        df = DataFrame(rows)

        self.setup_figure()

        scatterplot_kwargs: dict[str, Any] = {
            "data": df,
            "x": x,
            "y": y,
            "hue": hue,
            "palette": LunaColours.palette(df[hue].nunique()),
            "s": 60,
            "alpha": 0.8,
        }
        scatterplot_kwargs.update(kwargs)

        scatterplot(**scatterplot_kwargs)

        if hline:
            plt.axhline(y=hline, color=hcolor, linestyle="--", alpha=0.7, label=hline_label)

        self.finalize_plot(
            xlabel=xlabel,
            ylabel=ylabel,
            title=title,
            x_rotation=0,
            save_dir=save_dir,
        )
