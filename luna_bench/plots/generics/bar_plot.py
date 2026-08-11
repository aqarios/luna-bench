from __future__ import annotations

import logging
from abc import ABC
from typing import TYPE_CHECKING, Any, ClassVar

import numpy as np
import pandas as pd

from luna_bench.helpers.optional_dependencies import check_optional_dependency
from luna_bench.plots.dimensions import AlgorithmDimension, Dimension, MetricDimension
from luna_bench.plots.plot_style import Annotation, ErrorBars
from luna_bench.plots.utils import (
    AUTO_ERRORBAR,
    REFERENCE_LINE_COLOUR,
    Aggregation,
    ErrorBar,
    LunaColours,
    errorbar_label,
)

from .seaborn_plot import SeabornPlot

if TYPE_CHECKING:
    from logging import Logger

    from matplotlib.axes import Axes

    from luna_bench.custom import BenchmarkResultContainer

#: A line needs at least this many points to be a candidate error bar.
_MIN_LINE_POINTS = 2


class BarPlot(SeabornPlot, ABC):
    """Base helper for generating aggregated seaborn bar plots.

    Subclasses turn benchmark results into row dictionaries and hand them to
    :meth:`create`; everything below is shared configuration a user can set on any of
    them at construction time, grouped into bundles by what it configures, e.g.
    ``RuntimePlot(annotation=Annotation(enabled=False))``. The flat spelling those
    options used to have - ``annotate=False`` - is still accepted.

    Attributes
    ----------
    x : Dimension
        What the bars are - one per algorithm by default. Also titles the axis.
    y : MetricDimension
        What the bars measure - the attribute read off each result, and its axis title.
    aggregation : Aggregation
        Aggregation applied per x category, by default the mean over the models.
    errorbars : ErrorBars
        The error bars drawn on top of the bars: what they show, their colour, and the
        caps that turn them into a T.
    annotation : Annotation | None
        The values written above the bars, by default ``None`` - none are written.
    grouping : Dimension | None
        What splits each bar into a group of bars: `ModelDimension`, `AlgorithmDimension`,
        `FeatureDimension` or `ParameterDimension`.

    Examples
    --------
    Split the bars by a per-model category and write the figure for LaTeX:

    >>> plot = RuntimePlot(
    ...     grouping=FeatureDimension(feature=UseCaseFeature, label="Use case"),
    ...     figure=Figure(file_formats=("pgf", "png")),
    ... )
    >>> bench.add_plot(name="runtime", plot=plot)

    Requires
    --------
    Install the 'pre-defined' extra: ``pip install luna-bench[pre-defined]``

    See Also
    --------
    SeabornPlot : Figure size, output formats, and saving.
    """

    logger: ClassVar[Logger] = logging.getLogger(__name__)

    x: Dimension = AlgorithmDimension()
    """What the bars are: one per value of this dimension, and its title on the axis."""

    y: MetricDimension = MetricDimension("value")
    """What the bars measure: the attribute read off each result, and its title on the axis."""

    aggregation: Aggregation = Aggregation.MEAN
    """Aggregation applied to the values of an x category, by default their mean."""

    errorbars: ErrorBars | None = ErrorBars()
    """The error bars drawn on top of the bars: what they show, their colour and caps.

    ``None`` draws none, the same as ``ErrorBars(spec=None)``.
    """

    annotation: Annotation | None = None
    """The values written above the bars - how they are formatted and how large.

    ``None``, the default, writes none: a bar chart is read off its axis, and a number
    above every bar is worth its clutter only when the exact value is the point. Pass an
    `Annotation` to turn them on, empty for the defaults.
    """

    grouping: Dimension | None = None
    """What splits each bar into a group of bars.

    One of the groupers - `ModelDimension`, `AlgorithmDimension`, `FeatureDimension`,
    `ParameterDimension` - or ``None``, which leaves the bars ungrouped.
    """

    def apply_grouping(self, benchmark_results: BenchmarkResultContainer, rows: list[dict[str, Any]]) -> dict[str, Any]:
        """Split *rows* into groups along :attr:`grouping`.

        What that means is the grouper's business - a column of the plotted data, a value
        looked up per model, or a setting the algorithms were configured with - and so is
        deciding that it does not apply, in which case the bars stay ungrouped.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Benchmark data the feature results and algorithm configurations are read from.
        rows : list[dict[str, Any]]
            Row-oriented plot data, annotated - and, where a grouping applies to only part
            of the data, reduced - in place.

        Returns
        -------
        dict[str, Any]
            Keyword arguments to forward to :meth:`create`. Empty when no grouping
            applies, so call sites can splat it unconditionally.
        """
        if self.grouping is None or not rows:
            return {}

        column = self.grouping.resolve(benchmark_results, rows)
        if column is None:
            self.logger.warning("%s: plotting ungrouped", self.__class__.__name__)
            return {}

        return {"hue": column, "legend": True}

    def draw(
        self,
        *,
        benchmark_results: BenchmarkResultContainer,
        rows: list[dict[str, Any]],
        save_dir: str | None = None,
        **overrides: Any,
    ) -> None:
        """Group *rows* and draw them with the display configuration of this plot.

        This is what turns the declared fields - :attr:`x`, :attr:`title`, :attr:`hline`
        and the rest - into a :meth:`create` call, so a subclass only has to say which
        rows it plots. Doing it in one place is also what keeps :attr:`group_by` working
        for every bar plot rather than for those that remember to apply it.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Benchmark data, used to look up the groups of a feature :attr:`group_by`.
        rows : list[dict[str, Any]]
            Row-oriented plot data.
        save_dir : str | None, optional
            Directory to save the figure into, by default ``None``.
        **overrides : Any
            Keyword arguments forwarded to :meth:`create`, overriding the fields.
        """
        grouping = self.apply_grouping(benchmark_results, rows)

        # After the grouping, which may drop rows the x-axis would otherwise show. A
        # dimension that does not apply has said so; the bars then fall back to the column
        # it stands for, or to the algorithm, which every row of a benchmark carries.
        x_column = self.x.resolve(benchmark_results, rows) if rows else None

        create_kwargs: dict[str, Any] = {
            "save_dir": save_dir,
            "rows": self.transform_rows(rows, x_column, grouping.get("hue")),
            "x": x_column or getattr(self.x, "column", AlgorithmDimension.column),
            "y": self.y.column,
            "xlabel": self.x.title,
            "ylabel": self.y.title,
            "title": self.figure.title,
            "aggregation": self.aggregation,
            "errorbar": self.errorbars.spec if self.errorbars else None,
            "hline": self.y.reference,
            "hline_label": self.y.reference_label,
            "baseline": self.y.baseline,
            "ylim": self.y.limits,
        }
        create_kwargs.update(grouping)
        create_kwargs.update(overrides)

        self.create(**create_kwargs)

    def transform_rows(self, rows: list[dict[str, Any]], x: str | None, group: str | None) -> list[dict[str, Any]]:
        """Return the rows to plot, by default the rows as they are.

        A subclass that has to reduce its rows before they are drawn - pooling counts
        into a single ratio, say - overrides this rather than :meth:`run`, so it keeps
        the shared grouping and display handling. It is told what the bars and the groups
        turned out to be, since that is what a row has to keep to stay one of them.

        Parameters
        ----------
        rows : list[dict[str, Any]]
            Row-oriented plot data, already annotated with the dimensions' columns.
        x : str | None
            Column the bars are drawn per, or ``None`` when the plot has no rows.
        group : str | None
            Column the bars are split by, or ``None`` when they are ungrouped.

        Returns
        -------
        list[dict[str, Any]]
            The rows handed to :meth:`create`.
        """
        _ = x, group
        return rows

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
        errorbar: ErrorBar | str = AUTO_ERRORBAR,
        hue: str | None = None,
        hline: float | None = None,
        hline_label: str | None = None,
        hcolor: str = REFERENCE_LINE_COLOUR,
        baseline: float | None = None,
        ylim: tuple[float, float] | None = None,
        legend: bool = False,
        save_dir: str | None = None,
        **kwargs: Any,
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
        errorbar : ErrorBar | str, optional
            Seaborn error bar specification (``"sd"``, ``("ci", 95)``, ``None`` to
            disable). By default ``"auto"``, which takes the error bar from
            *aggregation*: the spread of the samples for means, none for min/max.
        hue : str | None, optional
            Optional grouping column for grouped bars, by default ``None``.
        hline : float | None, optional
            Optional horizontal reference line value, by default ``None``.
        hline_label : str | None, optional
            Legend label for the horizontal reference line, by default ``None``.
        hcolor : str, optional
            Colour of the horizontal reference line, by default black.
        baseline : float | None, optional
            Height of a solid black baseline marking where the bars start, by default
            ``None``. Unlike *hline* it carries no label and stays out of the legend -
            it says where zero is, it does not name a target.
        ylim : tuple[float, float] | None, optional
            Lower and upper y-axis limits, by default ``None``.
        legend : bool, optional
            Whether seaborn should create a legend for hue groups, by default ``False``.
        save_dir : str | None, optional
            Directory to save the figure into, by default ``None``.
        **kwargs : Any
            Additional keyword arguments forwarded to :func:`seaborn.barplot`. They
            override the defaults computed here, so anything seaborn understands
            (``palette``, ``saturation``, ``capsize``, ``err_kws``, ...) can be tuned
            from the call site.
        """
        check_optional_dependency("matplotlib")
        check_optional_dependency("seaborn")
        import seaborn as sns  # noqa: PLC0415
        from matplotlib import pyplot as plt  # noqa: PLC0415
        from matplotlib.lines import Line2D  # noqa: PLC0415

        if not rows:
            self.logger.warning(f"{self.__class__}: no data to plot")
            return

        df = pd.DataFrame(rows)
        errorbars = self.errorbars or ErrorBars(spec=None)
        resolved_errorbar = aggregation.errorbar if errorbar == AUTO_ERRORBAR else errorbar

        self.setup_figure()

        barplot_kwargs: dict[str, Any] = {
            "data": df,
            "x": x,
            "y": y,
            "estimator": aggregation.estimator,
            "errorbar": resolved_errorbar,
            "err_kws": {"color": str(errorbars.color), "linewidth": 1.5},
            # Seaborn dims a fill to 75% saturation by default, which turns the brand
            # blue into a colour that is nearly it. The palette is chosen, so it is drawn.
            "saturation": 1.0,
            "capsize": errorbars.capsize,
            "legend": legend,
            **self._color_kwargs(df, hue=hue),
        }
        barplot_kwargs.update(self.figure.seaborn_kwargs)
        barplot_kwargs.update(kwargs)

        sns.barplot(**barplot_kwargs)

        grouped = legend and hue is not None

        if self.annotation is not None:
            self._annotate_bars(plt.gca())
            ylim = self._with_headroom(ylim)

        handles: list[Any] = []
        labels: list[str] = []

        if grouped:
            handles, labels = plt.gca().get_legend_handles_labels()

        if hline is not None:
            line = plt.axhline(y=hline, color=hcolor, linestyle="--", alpha=0.7, label=hline_label)
            if hline_label:
                handles.append(line)
                labels.append(hline_label)

        if baseline is not None:
            # Solid and unlabelled, so it reads as the floor of the bars rather than as
            # a second target competing with the dashed reference line.
            plt.axhline(y=baseline, color=REFERENCE_LINE_COLOUR, linewidth=1.0)

        if resolved_errorbar is not None:
            handles.append(Line2D([], [], color=str(errorbars.color), marker="|", markersize=8, linestyle="none"))
            labels.append(errorbar_label(resolved_errorbar))

        if handles:
            # A group legend needs room of its own; a lone error bar entry fits inside the axes.
            placement = {"loc": "upper left", "bbox_to_anchor": (1.01, 1.0)} if grouped else {}
            plt.legend(handles=handles, labels=labels, title=hue if grouped else None, **placement)

        self.finalize_plot(xlabel, ylabel, title, ylim, save_dir=save_dir)

    def _annotate_bars(self, ax: Axes) -> None:
        """Write the aggregated value above every bar, clear of its error bar.

        Parameters
        ----------
        ax : Axes
            The axes seaborn drew the bars on.
        """
        from matplotlib.container import BarContainer  # noqa: PLC0415

        annotation = self.annotation or Annotation()
        error_tops = self._errorbar_tops(ax)

        for container in ax.containers:
            if not isinstance(container, BarContainer):
                continue

            for bar in container:
                height = bar.get_height()
                center = bar.get_x() + bar.get_width() / 2
                covered = [top for x, top in error_tops if bar.get_x() <= x <= bar.get_x() + bar.get_width()]

                ax.annotate(
                    self.annotation_text(height),
                    xy=(center, max([height, *covered])),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    rotation=annotation.rotation,
                    fontsize=annotation.fontsize,
                )

    def annotation_text(self, value: float) -> str:
        """Return the text written above a bar of *value*.

        Applies :attr:`annotate_format`, unless :attr:`annotate_max_decimals` allows the
        value to be written as a plain decimal instead of in scientific notation.

        Parameters
        ----------
        value : float
            The aggregated value of one bar.

        Returns
        -------
        str
            The annotation, e.g. ``"0.000057"`` rather than ``"5.67e-05"``.
        """
        annotation = self.annotation or Annotation()

        if annotation.max_decimals is None:
            return annotation.format.format(value)

        rounded = round(value, annotation.max_decimals)
        if rounded == 0 and value != 0:
            # Invisible at that many decimals, so writing it plainly would say "0".
            return annotation.format.format(value)

        text = f"{rounded:.{annotation.max_decimals}f}"
        return text.rstrip("0").rstrip(".") if "." in text else text

    @staticmethod
    def _errorbar_tops(ax: Axes) -> list[tuple[float, float]]:
        """Return the ``(x centre, upper end)`` of every error bar seaborn drew.

        Seaborn draws them as standalone lines rather than attaching them to the bar
        containers, so they have to be picked back off the axes to know how much room a
        bar's annotation needs. A capped error bar is one line covering both the stem
        and the two caps, so the centre comes from the x range rather than from a single
        point.

        Parameters
        ----------
        ax : Axes
            The axes seaborn drew the bars on.

        Returns
        -------
        list[tuple[float, float]]
            One entry per error bar found on the axes.
        """
        tops = []
        for line in ax.lines:
            xdata = np.asarray(line.get_xdata(), dtype=float)
            ydata = np.asarray(line.get_ydata(), dtype=float)
            if xdata.size != ydata.size:
                continue

            # The caps and the stem are separated by NaN gaps that carry no coordinate.
            drawn = np.isfinite(xdata) & np.isfinite(ydata)
            xs, ys = xdata[drawn], ydata[drawn]

            # An error bar rises; anything drawn at a constant height is a reference line.
            if xs.size < _MIN_LINE_POINTS or ys.min() == ys.max():
                continue

            tops.append((float((xs.min() + xs.max()) / 2), float(ys.max())))
        return tops

    def _with_headroom(self, ylim: tuple[float, float] | None) -> tuple[float, float] | None:
        """Grow the upper y limit so the annotations fit above the tallest bar.

        Parameters
        ----------
        ylim : tuple[float, float] | None
            The limits requested by the caller, or ``None`` to keep the data range.

        Returns
        -------
        tuple[float, float] | None
            The limits with :attr:`annotate_headroom` added on top. ``None`` is passed
            through; the data range is stretched with a matplotlib margin instead.
        """
        check_optional_dependency("matplotlib")
        from matplotlib import pyplot as plt  # noqa: PLC0415

        headroom = (self.annotation or Annotation()).headroom

        if ylim is None:
            plt.gca().margins(y=headroom)
            return None

        bottom, top = ylim
        return (bottom, top + (top - bottom) * headroom)

    def _color_kwargs(self, df: pd.DataFrame, *, hue: str | None) -> dict[str, Any]:
        """Return the seaborn colour arguments for the bars.

        Ungrouped bars all share one colour - :attr:`color` when set, the Aqarios blue
        otherwise - because a colour per x category would encode nothing the axis does
        not already say. The Luna gradient is reserved for grouped bars, where the
        colour carries the group.
        """
        if hue is None or hue not in df.columns:
            return {"color": str(self.figure.color or LunaColours.LUNA_SOLVE)}

        return {"hue": hue, "palette": LunaColours.palette(df[hue].nunique())}
