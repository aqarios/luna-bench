from __future__ import annotations

import logging
from abc import ABC
from typing import TYPE_CHECKING, Any, ClassVar

import numpy as np
import pandas as pd
from pydantic import field_serializer, field_validator

from luna_bench.custom.types import FeatureClass
from luna_bench.helpers.optional_dependencies import check_optional_dependency
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
    from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer

#: Group used for models the ``group_by`` feature has no result for.
UNGROUPED_LABEL = "unknown"

#: A line needs at least this many points to be a candidate error bar.
_MIN_LINE_POINTS = 2


class BarPlot(SeabornPlot, ABC):
    """Base helper for generating aggregated seaborn bar plots.

    Subclasses turn benchmark results into row dictionaries and hand them to
    :meth:`create`; everything below is shared configuration a user can set on any
    of them at construction time, e.g.
    ``AverageRuntimePlot(annotate=False, file_formats=("pgf", "png"))``.

    Attributes
    ----------
    color : str | None
        Single colour for ungrouped bars, by default the Aqarios blue. Ignored once
        :attr:`group_by` splits the bars, where the Luna gradient encodes the group.
    errorbar_color : str
        Colour of the error bars, by default ``LunaColours.SKY``.
    errorbar_capsize : float
        Width of the caps that turn an error bar into a T, as a share of the bar
        width, by default ``0.2``. ``0.0`` leaves a plain line.
    annotate : bool
        Write the aggregated value above each bar, by default ``True``.
    annotate_format : str
        Format applied to an annotated value, by default ``"{:.3g}"``.
    annotate_rotation : int
        Rotation of the annotations in degrees, by default ``0``.
    annotate_headroom : float
        Share of the y range added above the bars so the annotations fit, by default ``0.3``.
    group_by : FeatureClass | None
        Feature whose per-model value splits each bar into a group of bars, e.g. a use
        case or problem category assigned with a lookup feature. ``None`` (the default)
        leaves the bars ungrouped.
    group_label : str | None
        Legend title for *group_by*, by default the feature's class name without its
        ``"Feature"`` suffix.
    group_attribute : str
        Attribute read off the feature result, by default ``"value"`` - what the
        lookup features expose.

    Examples
    --------
    Split the bars by a per-model category and write the figure for LaTeX:

    >>> plot = AverageRuntimePlot(
    ...     group_by=UseCaseFeature,
    ...     group_label="Use case",
    ...     file_formats=("pgf", "png"),
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

    color: str | None = None
    """Single colour for ungrouped bars.

    ``None`` uses the Aqarios blue. Grouped bars ignore this and take the Luna gradient
    from blue over green to yellow, spread across the groups.
    """

    errorbar_color: str = LunaColours.SKY
    """Colour of the error bars drawn on top of the bars."""

    errorbar_capsize: float = 0.2
    """Width of the error bar caps as a share of the bar width.

    The caps give the bar its T shape, which reads as a range rather than as a stray
    vertical line. ``0.0`` draws a plain line without caps.
    """

    annotate: bool = True
    """Write the aggregated value above each bar, clear of its error bar."""

    annotate_format: str = "{:.3g}"
    """Format applied to an annotated value, e.g. ``"{:.1f}%"`` for percentages."""

    annotate_rotation: int = 0
    """Rotation of the annotations in degrees. Set to ``90`` when narrow bars make the labels collide."""

    annotate_headroom: float = 0.3
    """Share of the y range added above the bars so the annotations fit."""

    group_by: FeatureClass | None = None
    """Feature whose per-model value splits each bar into a group of bars.

    Typically a use case or problem category assigned with a lookup feature. Models the
    feature has no result for are grouped as ``"unknown"``; if no model has one, the
    plot falls back to ungrouped bars. ``None`` leaves the bars ungrouped.
    """

    group_label: str | None = None
    """Legend title for :attr:`group_by`, by default the feature's class name without its ``"Feature"`` suffix."""

    group_attribute: str = "value"
    """Attribute read off the feature result. ``"value"`` is what the lookup features expose."""

    @field_serializer("group_by")
    def _serialize_group_by(self, value: FeatureClass | None) -> str | None:
        """Store the grouping feature by id, since a class is not JSON.

        The plot configuration is persisted with the benchmark, so ``group_by`` has to
        survive a round trip through the database as the id the feature is registered
        under.
        """
        if value is None:
            return None
        return getattr(value, "registered_id", None) or f"{value.__module__}.{value.__qualname__}"

    @field_validator("group_by", mode="before")
    @classmethod
    def _resolve_group_by(cls, value: Any) -> Any:  # noqa: ANN401
        """Turn the id a stored configuration carries back into the feature class."""
        if not isinstance(value, str):
            return value

        from luna_bench.custom.registry_info import RegistryInfo  # noqa: PLC0415

        return RegistryInfo.get_feature_by_id(value)

    def apply_grouping(self, benchmark_results: BenchmarkResultContainer, rows: list[dict[str, Any]]) -> dict[str, Any]:
        """Split *rows* into groups along the :attr:`group_by` feature.

        Each row is expected to carry the model it belongs to under ``"model"``; the
        group value looked up for that model is added to the row in place.

        Parameters
        ----------
        benchmark_results : BenchmarkResultContainer
            Benchmark data the feature results are read from.
        rows : list[dict[str, Any]]
            Row-oriented plot data, annotated in place with the group column.

        Returns
        -------
        dict[str, Any]
            Keyword arguments to forward to :meth:`create`. Empty when no grouping
            applies, so call sites can splat it unconditionally.
        """
        if self.group_by is None or not rows:
            return {}

        groups = {
            model_name: self._group_value(container, self.group_by)
            for model_name, container in benchmark_results.features.items()
        }

        if all(value is None for value in groups.values()):
            self.logger.warning(
                "%s: no results for group feature %s, plotting ungrouped",
                self.__class__.__name__,
                self.group_by.__name__,
            )
            return {}

        label = self.group_label or self.group_by.__name__.removesuffix("Feature")
        for row in rows:
            row[label] = groups.get(str(row.get("model", ""))) or UNGROUPED_LABEL

        return {"hue": label, "legend": True}

    def _group_value(self, feature_results: FeatureResultContainer, feature_cls: FeatureClass) -> str | None:
        """Read the group value of a single model, or ``None`` when it has none."""
        try:
            result = feature_results.first(feature_cls)
        except Exception:  # A model without a result for the feature is simply ungrouped.
            return None

        value = getattr(result, self.group_attribute, None)
        return None if value is None else str(value)

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
        resolved_errorbar = aggregation.errorbar if errorbar == AUTO_ERRORBAR else errorbar

        self.setup_figure()

        barplot_kwargs: dict[str, Any] = {
            "data": df,
            "x": x,
            "y": y,
            "estimator": aggregation.estimator,
            "errorbar": resolved_errorbar,
            "err_kws": {"color": str(self.errorbar_color), "linewidth": 1.5},
            "capsize": self.errorbar_capsize,
            "legend": legend,
            **self._color_kwargs(df, hue=hue),
        }
        barplot_kwargs.update(kwargs)

        sns.barplot(**barplot_kwargs)

        grouped = legend and hue is not None

        if self.annotate:
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
            handles.append(Line2D([], [], color=str(self.errorbar_color), marker="|", markersize=8, linestyle="none"))
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

        error_tops = self._errorbar_tops(ax)

        for container in ax.containers:
            if not isinstance(container, BarContainer):
                continue

            for bar in container:
                height = bar.get_height()
                center = bar.get_x() + bar.get_width() / 2
                covered = [top for x, top in error_tops if bar.get_x() <= x <= bar.get_x() + bar.get_width()]

                ax.annotate(
                    self.annotate_format.format(height),
                    xy=(center, max([height, *covered])),
                    xytext=(0, 4),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    rotation=self.annotate_rotation,
                    fontsize="small",
                )

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

        if ylim is None:
            plt.gca().margins(y=self.annotate_headroom)
            return None

        bottom, top = ylim
        return (bottom, top + (top - bottom) * self.annotate_headroom)

    def _color_kwargs(self, df: pd.DataFrame, *, hue: str | None) -> dict[str, Any]:
        """Return the seaborn colour arguments for the bars.

        Ungrouped bars all share one colour - :attr:`color` when set, the Aqarios blue
        otherwise - because a colour per x category would encode nothing the axis does
        not already say. The Luna gradient is reserved for grouped bars, where the
        colour carries the group.
        """
        if hue is None or hue not in df.columns:
            return {"color": str(self.color or LunaColours.LUNA_SOLVE)}

        return {"hue": hue, "palette": LunaColours.palette(df[hue].nunique())}
