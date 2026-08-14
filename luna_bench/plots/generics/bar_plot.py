from __future__ import annotations

import logging
from abc import ABC
from typing import TYPE_CHECKING, Any, ClassVar

import numpy as np
import pandas as pd

from luna_bench.helpers.optional_dependencies import check_optional_dependency
from luna_bench.plots.dimensions import PERCENT, AlgorithmDimension, Dimension, MetricDimension
from luna_bench.plots.plot_style import Annotation, ErrorBars
from luna_bench.plots.utils import (
    AUTO_ERRORBAR,
    REFERENCE_LINE_COLOUR,
    Aggregation,
    ErrorBar,
    LunaColours,
    errorbar_label,
)

from .seaborn_plot import MISSING_MARKER, SeabornPlot, missing_label

if TYPE_CHECKING:
    from logging import Logger

    from matplotlib.axes import Axes
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch

    from luna_bench.custom import BenchmarkResultContainer

#: A line needs at least this many points to be a candidate error bar.
_MIN_LINE_POINTS = 2

#: Width of an x slot with no bar in it to measure, in data coordinates.
_FULL_SLOT_WIDTH = 0.8

#: Height of the mark for the values that could not be drawn, as a share of the axes.
_MISSING_MARK_HEIGHT = 0.02

#: Room left above the tallest thing drawn when it reaches the limits the plot asked for,
#: as a share of them: a cap or a reference line exactly at the top would otherwise be
#: drawn onto the frame and read as part of it.
_TOP_MARGIN = 0.05

#: How a value read off a percent axis is annotated, unless a format was asked for.
PERCENT_FORMAT = "{:.1f}%"


def _distinct(df: pd.DataFrame, column: str | None) -> list[str]:
    """Return the values of *column* as strings, once each, in the order they appear."""
    if column is None or column not in df:
        return []
    return list(dict.fromkeys(df[column].astype(str)))


def _categorical_order(
    missing: dict[tuple[str, str], int], order: list[str], hue_order: list[str]
) -> dict[str, list[str]]:
    """Return the categories to name on the seaborn call, when something is missing.

    A bar whose every value was dropped has no rows left to put it on the axis, and its
    mark would land on whichever bar took its place. Naming the categories and the groups
    keeps the slot - and the order the rows arrived in.

    Parameters
    ----------
    missing : dict[tuple[str, str], int]
        Number of missing values per category and group; nothing is named when it is empty.
    order : list[str]
        The x categories, in the order they appear in the data.
    hue_order : list[str]
        The groups, in the order they appear in the data. Empty when the bars are ungrouped.

    Returns
    -------
    dict[str, list[str]]
        The ``order`` and ``hue_order`` arguments, as far as they apply.
    """
    if not missing:
        return {}
    return {name: values for name, values in (("order", order), ("hue_order", hue_order)) if values}


#: How a category that lost values is struck through, on the axes and in the legend.
_STRIKE_STYLE: dict[str, Any] = {
    "facecolor": str(LunaColours.ROCKET_FIRE),
    "alpha": 0.12,
    "hatch": "//",
    "edgecolor": str(LunaColours.ROCKET_FIRE),
    "linewidth": 0.0,
}


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

        if not rows:
            self.logger.warning(f"{self.__class__}: no data to plot")
            return

        full = pd.DataFrame(rows)
        df, missing = self.resolve_missing(full, y, by=x, within=hue)
        if df.empty:
            self.logger.warning("%s: every value is missing or not finite, nothing to plot", type(self).__name__)
            return

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
            # Coloured from the whole frame rather than the drawn one: the groups on the
            # axis are the ones the rows arrived with, including any that lost every value.
            **self._color_kwargs(full, hue=hue),
        }
        order = _distinct(full, x)
        hue_order = _distinct(full, hue)
        for name, categories in _categorical_order(missing, order, hue_order).items():
            barplot_kwargs.setdefault(name, categories)

        barplot_kwargs.update(self.figure.seaborn_kwargs)
        barplot_kwargs.update(kwargs)

        sns.barplot(**barplot_kwargs)

        if missing and order:
            # A category with no bar has no artist either, and the x range would shrink
            # around the ones that were drawn - taking the empty slot, which is the whole
            # statement of "drop", out of the figure.
            plt.gca().set_xlim(-0.5, len(order) - 0.5)

        missing_handle = self._mark_missing(plt.gca(), missing, order, hue_order)

        grouped = legend and hue is not None

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

        self._legend_extras(handles, labels, errorbars, resolved_errorbar, missing_handle, missing)
        self._draw_legend(plt.gca(), handles, labels, title=hue if grouped else None)

        if self.annotation is not None:
            self._annotate_bars(plt.gca())

        # Grown last, so the range already covers the reference and the baseline.
        ylim = self._with_headroom(ylim, reference=hline)

        self.finalize_plot(xlabel, ylabel, title, ylim, save_dir=save_dir)

    def _draw_legend(self, axes: Axes, handles: list[Any], labels: list[str], *, title: str | None) -> None:
        """Put the key beside the axes, titled by what splits the bars if anything does.

        Parameters
        ----------
        axes : Axes
            The axes the bars were drawn on.
        handles : list[Any]
            Legend handles; nothing is drawn when there are none.
        labels : list[str]
            Their labels.
        title : str | None
            What the groups are, for a grouped plot.
        """
        if not handles:
            return

        if title is not None:
            axes.legend(handles=handles, labels=labels, title=title)

        self.place_legend(axes, handles, labels)

    @staticmethod
    def _legend_extras(  # noqa: PLR0913, PLR0917
        handles: list[Any],
        labels: list[str],
        errorbars: ErrorBars,
        errorbar: ErrorBar,
        missing_handle: Line2D | tuple[Patch, Line2D] | None,
        missing: dict[tuple[str, str], int],
    ) -> None:
        """Add the entries that explain the marks seaborn did not draw itself.

        Parameters
        ----------
        handles : list[Any]
            Legend handles, extended in place.
        labels : list[str]
            Legend labels, extended in place alongside *handles*.
        errorbars : ErrorBars
            The error bar options, for the colour of its legend entry.
        errorbar : ErrorBar
            What the error bars show, or ``None`` when none were drawn.
        missing_handle : Line2D | tuple[Patch, Line2D] | None
            The mark for the values that could not be drawn, if any were.
        missing : dict[tuple[str, str], int]
            Number of missing values per category and group, for the count in the label.
        """
        from matplotlib.lines import Line2D  # noqa: PLC0415

        if errorbar is not None:
            handles.append(Line2D([], [], color=str(errorbars.color), marker="|", markersize=8, linestyle="none"))
            labels.append(errorbar_label(errorbar))

        if missing_handle is not None:
            handles.append(missing_handle)
            labels.append(missing_label(missing))

    def _mark_missing(
        self, ax: Axes, missing: dict[tuple[str, str], int], order: list[str], hue_order: list[str]
    ) -> Line2D | tuple[Patch, Line2D] | None:
        """Mark the categories whose values could not be drawn, and say how many.

        A red cross on the axis under the category, with the number of values behind it
        written above the cross. Where an algorithm lost every value, the cross stands on
        its own with no bar next to it - which is the whole point of drawing it.

        Under ``Missing(policy="mark")`` the category is struck through as well, over the
        full height of the axes: an empty slot says "no bar here", a struck one says the
        solver was asked and reported nothing. Under ``"drop"`` nothing is drawn at all -
        the empty slot is the statement.

        Parameters
        ----------
        ax : Axes
            The axes seaborn drew the bars on.
        missing : dict[tuple[str, str], int]
            Number of missing values per category and group, as counted by
            :meth:`SeabornPlot.resolve_missing`.
        order : list[str]
            The x categories, in the order they are drawn.
        hue_order : list[str]
            The groups within each category, in the order they are drawn. Empty when the
            bars are ungrouped.

        Returns
        -------
        Line2D | tuple[Patch, Line2D] | None
            A legend handle for the mark - the cross, and the band behind it where the
            category was struck through - or ``None`` when nothing was missing.
        """
        from matplotlib.lines import Line2D  # noqa: PLC0415
        from matplotlib.patches import Patch  # noqa: PLC0415

        if not missing or not self.missing.mark or self.missing.policy == "drop":
            # "drop" leaves the slot empty and says nothing more: the values are out of
            # the averages, and a figure about what the algorithms did report has no cross
            # to carry. The warning in the log still names them.
            return None

        annotation = self.annotation or Annotation()
        # x in data coordinates, y as a share of the axes height, so the marks sit just
        # above the axis whatever the values turn out to be.
        transform = ax.get_xaxis_transform()
        struck = self.missing.policy == "mark"

        marked = False
        for (category, group), count in missing.items():
            slot = self._slot_at(ax, order, hue_order, category, group)
            if slot is None:
                # Not on the axes at all: the warning already said how many values were
                # lost, and a mark with nothing under it would only be misleading.
                continue

            position, width = slot

            if struck:
                # The slot's own width, so a group that kept its values is not struck
                # through with the one next to it. Over the whole height rather than up
                # to a value, since there is none.
                ax.axvspan(position - width / 2, position + width / 2, zorder=0, **_STRIKE_STYLE)

            ax.plot(
                [position],
                [_MISSING_MARK_HEIGHT],
                marker="x",
                markersize=9,
                markeredgewidth=2.0,
                linestyle="none",
                color=str(LunaColours.ROCKET_FIRE),
                transform=transform,
                clip_on=False,
                zorder=5,
            )
            ax.annotate(
                str(count),
                xy=(position, _MISSING_MARK_HEIGHT),
                xycoords=transform,
                xytext=(0, 9),
                textcoords="offset points",
                ha="center",
                va="bottom",
                color=str(LunaColours.ROCKET_FIRE),
                fontsize=annotation.fontsize,
                fontweight="bold",
                # The count sits over a bar as often as not, and red on the brand blue is
                # not a reading experience. A card behind it is.
                bbox={"boxstyle": "round,pad=0.2", "facecolor": "white", "edgecolor": "none", "alpha": 0.8},
                zorder=5,
            )
            marked = True

        if not marked:
            return None

        cross = Line2D([], [], **MISSING_MARKER)

        if not struck:
            return cross

        # The swatch carries the band as well, so the legend shows what a category that
        # lost values looks like rather than only the cross standing on the axis.
        return (Patch(**_STRIKE_STYLE), cross)

    @staticmethod
    def _slot_at(
        ax: Axes, order: list[str], hue_order: list[str], category: str, group: str
    ) -> tuple[float, float] | None:
        """Return the centre and the width of the bar drawn for *category* and *group*.

        Read off the bar itself where there is one: seaborn draws one container per group,
        each holding the categories in the order both were given, which is why they are
        named whenever something is missing. A category that lost *every* value keeps its
        tick but gets no rectangle, and that is the one worth marking - so its slot is
        reconstructed from the tick and the width of a bar that was drawn.

        Parameters
        ----------
        ax : Axes
            The axes seaborn drew the bars on.
        order : list[str]
            The x categories, in the order they are drawn.
        hue_order : list[str]
            The groups, in the order they are drawn. Empty when the bars are ungrouped.
        category : str
            The x category to find.
        group : str
            The group within it, or ``""`` when the bars are ungrouped.

        Returns
        -------
        tuple[float, float] | None
            The centre and width of the slot, or ``None`` when it is not on the axes.
        """
        from matplotlib.container import BarContainer  # noqa: PLC0415

        containers = [container for container in ax.containers if isinstance(container, BarContainer)]
        row = hue_order.index(group) if group in hue_order else 0
        column = order.index(category) if category in order else -1

        if column < 0:
            return None

        # Only when every slot was drawn does a container index mean the group it looks
        # like: seaborn leaves out the bars it had no rows for, and then the containers
        # have shifted under the groups that remain.
        groups = len(hue_order) or 1
        complete = len(containers) == groups and all(len(container) == len(order) for container in containers)

        if complete:
            bar = containers[row][column]
            return bar.get_x() + bar.get_width() / 2, bar.get_width()

        ticks = {
            label.get_text(): float(tick) for tick, label in zip(ax.get_xticks(), ax.get_xticklabels(), strict=False)
        }
        tick = ticks.get(category)
        if tick is None:
            return None

        width = next((bar.get_width() for container in containers for bar in container), _FULL_SLOT_WIDTH / groups)

        # Seaborn dodges the groups across the slot without a gap, so the one that was not
        # drawn sits where its neighbours leave room for it.
        offset = (row - (groups - 1) / 2) * width if hue_order else 0.0
        return tick + offset, width

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
                if not np.isfinite(height):
                    # A category that kept its slot without keeping a value: the cross
                    # under it says what happened, an annotated "nan" would not.
                    continue

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
        value to be written as a plain decimal instead of in scientific notation. A value
        read off a percent axis is written as a percentage, so the annotation says the
        same thing as the axis it stands on - unless a format was asked for, which wins.

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

        # Compared against the default rather than asking whether the field was set: a
        # bundle merged over a plot's own default carries every field as set, so that
        # would never be false for a plot that declares an annotation of its own.
        if self.y.scale == PERCENT and annotation.format == Annotation.model_fields["format"].default:
            return PERCENT_FORMAT.format(value)

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

    def _with_headroom(
        self, ylim: tuple[float, float] | None, *, reference: float | None = None
    ) -> tuple[float, float] | None:
        """Grow the upper y limit so everything drawn above the bars is inside the frame.

        Only the upper limit: the room is for what sits on top - the error bars, the
        reference line, the annotations - while a margin below the bars is empty axes
        saying a value could have been there.

        A plot with limits of its own keeps them as the *scale* - a ratio that cannot pass
        100% is not given ticks past it - and the room is added beyond the last tick, so
        what stands above the limit is inside the frame without the axis claiming a range
        the metric cannot reach. A share whose spread reaches past 100% is the usual case:
        the cap of its error bar is a fact about the run, and an axis that stops at the
        limit would cut it off. Without limits the range matplotlib scaled to the data is
        grown instead, read after everything is drawn so the reference line and the
        baseline are inside it.

        Parameters
        ----------
        ylim : tuple[float, float] | None
            The limits requested by the caller, or ``None`` to grow the data range.
        reference : float | None, optional
            Height of the reference line, by default ``None``. A line exactly at the
            limit would be drawn onto the frame and read as part of it.

        Returns
        -------
        tuple[float, float] | None
            The limits to apply, with the room above added on top.
        """
        check_optional_dependency("matplotlib")
        from matplotlib import pyplot as plt  # noqa: PLC0415

        axes = plt.gca()
        # No annotations means no labels to fit, and the room they need is theirs: what is
        # added below is only what it takes to show what was drawn.
        headroom = self.annotation.headroom if self.annotation is not None else 0.0

        if ylim is None:
            axes.autoscale_view()
            bottom, top = axes.get_ylim()
            return (bottom, top + (top - bottom) * headroom)

        bottom, top = ylim
        # The ticks the requested range would have, fixed before the room above is added
        # so that room stays unlabelled: the axis reads 0 to 100, and what stands above it
        # has somewhere to be.
        axes.set_ylim(bottom, top)
        axes.set_yticks([tick for tick in axes.get_yticks() if bottom <= tick <= top])

        span = top - bottom
        drawn = self._drawn_top(axes, reference=reference)
        if drawn is not None and drawn >= top:
            top = drawn + span * _TOP_MARGIN

        return (bottom, top + span * headroom)

    def _drawn_top(self, axes: Axes, *, reference: float | None) -> float | None:
        """Return the highest point the plot put on *axes*, or ``None`` if it drew nothing.

        Parameters
        ----------
        axes : Axes
            The axes seaborn drew the bars on.
        reference : float | None
            Height of the reference line, if there is one.

        Returns
        -------
        float | None
            The topmost of the bars, their error bars and the reference line.
        """
        from matplotlib.container import BarContainer  # noqa: PLC0415

        tops = [top for _, top in self._errorbar_tops(axes)]
        tops += [
            bar.get_height()
            for container in axes.containers
            if isinstance(container, BarContainer)
            for bar in container
            if np.isfinite(bar.get_height())
        ]
        if reference is not None:
            tops.append(reference)

        return max(tops) if tops else None

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
