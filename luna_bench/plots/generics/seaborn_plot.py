"""Shared seaborn-oriented plot infrastructure with figure, axis, and save support."""

from __future__ import annotations

import shutil
from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, get_args

import numpy as np
import pandas as pd
from pydantic import PrivateAttr, model_validator

from luna_bench.custom import BasePlot
from luna_bench.errors.components.plots.plot_missing_values_error import PlotMissingValuesError
from luna_bench.helpers.optional_dependencies import check_optional_dependency
from luna_bench.logging import BenchLogger
from luna_bench.plots.dimensions import (
    AlgorithmDimension,
    Dimension,
    FeatureDimension,
    ModelDimension,
    ParameterDimension,
)
from luna_bench.plots.plot_style import Figure, Missing, OptionBundle, PlotStyle, Theme
from luna_bench.plots.utils import LunaColours

if TYPE_CHECKING:
    from logging import Logger

    from matplotlib.axes import Axes

    from luna_bench.custom import BenchmarkResultContainer

#: Where the legend is anchored, in axes coordinates: just outside the right edge, top.
_LEGEND_ANCHOR = (1.01, 1.0)

#: How the values a figure could not draw are marked, in the colour they are marked in.
MISSING_MARKER: dict[str, Any] = {
    "color": str(LunaColours.ROCKET_FIRE),
    "marker": "x",
    "markersize": 8,
    "markeredgewidth": 2.0,
    "linestyle": "none",
}

#: Extensions stripped from ``figure_filename`` before the output format is appended.
KNOWN_FILE_FORMATS = frozenset({"eps", "jpeg", "jpg", "pdf", "pgf", "png", "ps", "svg", "svgz", "tif", "tiff", "webp"})


def missing_label(missing: dict[tuple[str, str], int]) -> str:
    """Return the legend label for the values a figure could not draw.

    Parameters
    ----------
    missing : dict[tuple[str, str], int]
        Number of missing values per category and group.

    Returns
    -------
    str
        The label, e.g. ``"missing values (3)"``.
    """
    return f"missing values ({sum(missing.values())})"


def _merge_styles(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    """Return *base* with *over* applied, merging the bundles they both carry.

    A style installed for the benchmark and one handed to a single plot are combined
    option by option rather than bundle by bundle, so a plot that says ``dpi=200`` in its
    own figure keeps the width the benchmark asked for.

    Parameters
    ----------
    base : dict[str, Any]
        The options of the less specific style.
    over : dict[str, Any]
        The options of the more specific one.

    Returns
    -------
    dict[str, Any]
        The combined options.
    """
    merged = dict(base)
    for name, value in over.items():
        previous = merged.get(name)
        if isinstance(value, OptionBundle) and isinstance(previous, OptionBundle):
            merged[name] = type(value).model_validate(previous.model_dump() | value.given())
        else:
            merged[name] = value
    return merged


def _bundle_of(annotation: Any) -> type[OptionBundle] | None:  # noqa: ANN401
    """Return the bundle a field holds, looking through an optional annotation.

    Parameters
    ----------
    annotation : Any
        The declared type of a field.

    Returns
    -------
    type[OptionBundle] | None
        The bundle class, or ``None`` for a field that holds something else.
    """
    candidates = get_args(annotation) or (annotation,)
    for candidate in candidates:
        if isinstance(candidate, type) and issubclass(candidate, OptionBundle):
            return candidate
    return None


def _labels(df: pd.DataFrame, column: str | None) -> list[str]:
    """Return the value of *column* per row as a string, or ``""`` per row without one."""
    if column is None or column not in df:
        return [""] * len(df)
    return [str(value) for value in df[column]]


def _describe(key: tuple[str, str], count: int) -> str:
    """Return one entry of the warning, naming the category and the group it is in."""
    category, group = key
    where = f"{category} / {group}" if group else category
    return f"{where or 'ungrouped'}: {count}"


def _became_of(policy: float | str, fill: float | None) -> str:
    """Return what became of the values a plot could not draw, as the note words it.

    Parameters
    ----------
    policy : float | str
        The policy that was applied to them.
    fill : float | None
        The value they were drawn at, or ``None`` when they were left out.

    Returns
    -------
    str
        A phrase completing "n of m values missing, ...".
    """
    if policy == "mark":
        return "left out and marked"
    return "left out" if fill is None else f"drawn at {fill:g}"


def _grouper_from_flat_names(data: dict[str, Any]) -> Dimension | None:
    """Build the grouper the flat ``group*`` options mean, if any were given.

    ``group_by`` used to take a column, a feature class or an algorithm setting and tell
    them apart by trying each in turn, which is how a configuration written or stored
    before the groupers spells its grouping.

    Parameters
    ----------
    data : dict[str, Any]
        The arguments the plot is being constructed from. The flat options are taken out.

    Returns
    -------
    Dimension | None
        The grouper, or ``None`` when no flat option was given.
    """
    by = data.pop("group_by", None)
    label = data.pop("group_label", None)
    attribute = data.pop("group_attribute", None)
    parameter = data.pop("group_parameter", None)

    if isinstance(by, type):
        return FeatureDimension(feature=by, label=label, **({"attribute": attribute} if attribute else {}))

    column = {grouper.column: grouper for grouper in (ModelDimension, AlgorithmDimension)}.get(str(by))
    if column is not None:
        return column(label=label)

    parameter = parameter or (by if isinstance(by, str) else None)
    return ParameterDimension(parameter=parameter, label=label) if parameter else None


class SeabornPlot(BasePlot, ABC):
    r"""Base of a seaborn-oriented plot with a shared figure and axis configuration.

    Every attribute below can be set when the plot is constructed, e.g.
    ``RuntimePlot(figure=Figure(width=12, file_formats=("pgf", "png")))``. The flat
    spelling those options used to have - ``width=12`` - is still accepted.

    Attributes
    ----------
    figure : Figure
        The figure this plot is drawn on and the files written from it - its size,
        resolution, output formats, and whether it is opened in a window.
    theme : Theme | None
        The seaborn theme the figure is drawn under and the gridlines behind the marks.
        By default seaborn's ``whitegrid`` with lines along the value axis; ``None`` for
        matplotlib's own look, without a grid.
    missing : Missing
        What becomes of the values the plot cannot draw - an infinite time to solution,
        a metric that failed - and how the figure says they were there.

    Requires
    --------
    Install the 'pre-defined' extra: ``pip install luna-bench[pre-defined]``
    """

    figure: Figure = Figure()
    """The figure this plot is drawn on and the files written from it."""

    theme: Theme | None = Theme()
    """The seaborn theme the figure is drawn under, and the gridlines behind the marks.

    A figure is read against its axis, so it is drawn with the lines that make that
    possible unless asked otherwise. ``None`` takes the theme and the grid away.
    """

    missing: Missing = Missing()
    """What becomes of the values the plot cannot draw, and how it says they were there."""

    logger: ClassVar[Logger] = BenchLogger.get_logger(__name__)

    _shared_axes: Any = PrivateAttr(default=None)
    """Axes this plot draws into instead of a figure of its own, see :meth:`draw_into`."""

    option_bundles: ClassVar[dict[str, type[OptionBundle]]] = {"style": PlotStyle}
    """Constructor arguments that configure several fields at once, and the bundle each takes.

    A ``style`` is spread over the bundle fields rather than stored, so a benchmark can
    hand the same look to every plot while each keeps what it says itself. Applied least
    specific first: the shared ``style``, then a bundle passed to the plot, then a flat
    option.
    """

    @model_validator(mode="before")
    @classmethod
    def _apply_option_bundles(cls, data: Any) -> Any:  # noqa: ANN401
        """Fold a shared style and the flat option names into the bundle fields.

        Three spellings reach the same option, from least to most specific: the ``style``
        a benchmark shares, a bundle passed to this plot, and a flat keyword such as
        ``width=12`` - the name every option had before the bundles, still accepted so
        that existing code and stored configurations keep working.

        Parameters
        ----------
        data : Any
            The arguments the plot is being constructed from.

        Returns
        -------
        Any
            The same arguments with every spelling folded into the bundle it belongs to.

        Raises
        ------
        TypeError
            If a bundle argument was given something other than the bundle it takes.
        """
        if not isinstance(data, dict):
            return data

        data = dict(data)
        # Least specific first: the style installed for the whole benchmark, the style
        # handed to this plot, its bundles, and finally a flat option.
        styles = [PlotStyle.installed(), cls._bundle_argument(data, "style", PlotStyle)]
        shared: dict[str, Any] = {}
        for style in styles:
            if style is not None:
                shared = _merge_styles(shared, style.given())

        legacy = _grouper_from_flat_names(data)
        if legacy is not None:
            data.setdefault("grouping", legacy)

        # ``annotate=False`` is how turning the annotations off was spelled before the
        # bundles; now they are turned off by not having any.
        if data.pop("annotate", True) is False:
            data["annotation"] = None

        for name, field in cls.model_fields.items():
            bundle_cls = _bundle_of(field.annotation)
            if bundle_cls is not None:
                cls._merge_bundle_field(data, name, bundle_cls, field.default, shared.get(name))

        # What the style says about a bundle the plot said nothing about, which is how a
        # shared ``theme=None`` reaches a plot: there is no bundle to merge, so the
        # decision itself is what carries over.
        return {key: value for key, value in shared.items() if key in cls.model_fields and key not in data} | data

    @classmethod
    def _merge_bundle_field(
        cls,
        data: dict[str, Any],
        name: str,
        bundle_cls: type[OptionBundle],
        declared: Any,  # noqa: ANN401
        shared: Any,  # noqa: ANN401
    ) -> None:
        """Fold everything said about one bundle field into the bundle it holds.

        Parameters
        ----------
        data : dict[str, Any]
            The arguments the plot is being constructed from, updated in place.
        name : str
            Name of the field.
        bundle_cls : type[OptionBundle]
            The bundle the field holds.
        declared : Any
            The default the plot class declares for it.
        shared : Any
            What the styles say about it, if anything.
        """
        if name in data and data[name] is None:
            # Said explicitly, so it wins over the shared style rather than reading as
            # "nothing said about it": no annotations, no error bars, no grouping.
            return

        given = [
            source.given()
            for source in (shared, cls._bundle_argument(data, name, bundle_cls))
            if isinstance(source, OptionBundle)
        ]
        given.append({field: data.pop(flat) for flat, field in bundle_cls.flat_names().items() if flat in data})

        merged: dict[str, Any] = {}
        for options in given:
            merged.update(options)

        if merged:
            # Merged over the default the plot class declares, so a subclass keeps the
            # options it set - the percent format of a share, say - unless asked otherwise.
            default = declared if isinstance(declared, OptionBundle) else bundle_cls()
            data[name] = bundle_cls.model_validate(default.model_dump() | merged)

    @staticmethod
    def _bundle_argument(data: dict[str, Any], name: str, expected: type[OptionBundle]) -> OptionBundle | None:
        """Take one bundle argument out of *data*, checking it is the bundle it should be.

        Parameters
        ----------
        data : dict[str, Any]
            The arguments the plot is being constructed from.
        name : str
            Name of the argument.
        expected : type[OptionBundle]
            The bundle the argument takes.

        Returns
        -------
        OptionBundle | None
            The bundle, or ``None`` when the argument was not given.

        Raises
        ------
        TypeError
            If the argument was given something other than *expected*.
        """
        bundle = data.pop(name, None) if name == "style" else data.get(name)
        if bundle is None or isinstance(bundle, dict):
            return None
        if not isinstance(bundle, expected):
            msg = f"'{name}' takes a {expected.__name__}, got {type(bundle).__name__}"
            raise TypeError(msg)
        return bundle

    def draw_into(self, axes: Axes, benchmark_results: BenchmarkResultContainer) -> None:
        """Run this plot onto an existing axes rather than into a figure of its own.

        Everything the plot draws goes through the pyplot state, so making that axes the
        current one is enough to redirect it. The figure, the files, and the window stay
        the caller's business - which is what lets several plots share one figure, e.g.
        the summary grid.

        Parameters
        ----------
        axes : Axes
            The axes to draw on.
        benchmark_results : BenchmarkResultContainer
            Aggregated benchmark data handed to :meth:`run`.
        """
        check_optional_dependency("matplotlib")
        from matplotlib import pyplot as plt  # noqa: PLC0415

        previous = self._shared_axes
        self._shared_axes = axes
        try:
            plt.sca(axes)
            self.run(benchmark_results)
        finally:
            self._shared_axes = previous

    def resolve_missing(
        self, df: pd.DataFrame, column: str, *, by: str | None = None, within: str | None = None
    ) -> tuple[pd.DataFrame, dict[tuple[str, str], int]]:
        """Return the drawable rows and how many of them were not, per category.

        A metric with nothing to report says so with a ``None`` or an infinity - a time
        to solution of a run that never reached the optimum is the usual one, since the
        expected time to something that did not happen is unbounded. Neither is a height
        a bar can have, and leaving them in poisons the aggregate: one infinity turns the
        mean of an algorithm into an infinity, and a missing value silently shortens it.

        What happens to them is :attr:`missing`, and by default it is nothing: the plot
        raises rather than quietly showing a mean over fewer models than it claims. Asked
        to carry on, it either leaves them out or fills them from the values that could be
        drawn - ``Missing(policy="max")`` puts them just past the tallest bar, which is
        where "worse than everything here" belongs. Either way they are counted and a
        warning is logged: a bar resting on half its models is a different statement from
        one resting on all of them, and that is not visible in the bar itself.

        Parameters
        ----------
        df : pd.DataFrame
            The plotting data.
        column : str
            Column holding the plotted value.
        by : str | None, optional
            Column whose categories the missing values are counted per, e.g. the x-axis
            of a bar plot. Without one they are counted under ``""``.
        within : str | None, optional
            Column that splits those categories further, e.g. the grouping of a bar plot.
            Counting per group is what lets a figure mark the one bar of a group that lost
            values rather than the whole category it sits in.

        Returns
        -------
        tuple[pd.DataFrame, dict[tuple[str, str], int]]
            The rows to draw, and the number of missing values per category and group -
            the group is ``""`` where there is none. The mapping is empty when nothing
            was missing.

        Raises
        ------
        PlotMissingValuesError
            If values are missing and the policy is ``"raise"``.
        """
        if column not in df:
            return df, {}

        values = pd.to_numeric(df[column], errors="coerce")
        finite = np.isfinite(values.to_numpy(dtype=float, na_value=np.nan))

        if bool(finite.all()):
            return df, {}

        absent = df[~finite]
        categories = _labels(absent, by)
        groups = _labels(absent, within)

        missing: dict[tuple[str, str], int] = {}
        for category, group in zip(categories, groups, strict=True):
            missing[category, group] = missing.get((category, group), 0) + 1

        described = ", ".join(_describe(key, count) for key, count in missing.items()) or "ungrouped"

        if self.missing.policy == "raise":
            raise PlotMissingValuesError(type(self).__name__, column, len(absent), len(df), described)

        fill = self._fill_value(values[finite])
        self.logger.warning(
            "%s: %d of %d values of '%s' are missing or not finite and are %s (%s)",
            type(self).__name__,
            len(absent),
            len(df),
            column,
            _became_of(self.missing.policy, fill),
            described,
        )

        if fill is None:
            return df[finite], missing

        filled = df.copy()
        filled[column] = values.where(finite, fill)
        return filled, missing

    def _fill_value(self, finite: pd.Series) -> float | None:
        """Return the value the missing ones are drawn at, or ``None`` to drop them.

        Parameters
        ----------
        finite : pd.Series
            The values that could be drawn, which an aggregate fill is derived from.

        Returns
        -------
        float | None
            The fill, or ``None`` when there is none - either because they are dropped,
            or because nothing was drawable to derive one from.
        """
        policy = self.missing.policy
        if policy in {"drop", "mark"}:
            # Both leave the value out; "mark" additionally shows where it was, which is
            # the mark's business rather than the fill's.
            return None
        if not isinstance(policy, str):
            return float(policy)
        if finite.empty:
            # Nothing survived to place them against, so there is nowhere to put them.
            return None

        # Pandas' own aggregates, by the name they carry there: the fill is a statement
        # about the values that made it into the plot, e.g. "just past the tallest bar".
        return float(finite.agg(policy)) * self.missing.factor

    def place_legend(self, axes: Axes, handles: list[Any] | None = None, labels: list[str] | None = None) -> None:
        """Put the legend beside the axes, whatever drew it.

        Outside the axes for a figure of its own: a legend inside sits on top of the data,
        and which corner is free depends on the run rather than on the plot - the figure
        would move its own key around as the numbers change. Beside it, the key is always
        in the same place and covers nothing.

        A panel of someone else's figure is the exception. The room beside it belongs to
        the panel next to it, so a key anchored there is drawn over a neighbour rather than
        over the data; inside the panel it stays within the space the plot was given.

        Parameters
        ----------
        axes : Axes
            The axes the plot was drawn on.
        handles : list[Any] | None, optional
            Legend handles, by default the ones already on the axes.
        labels : list[str] | None, optional
            Their labels, by default the ones already on the axes.
        """
        from matplotlib.legend_handler import HandlerTuple  # noqa: PLC0415

        existing = axes.get_legend()
        title = existing.get_title().get_text() if existing is not None else None

        if handles is None or labels is None:
            handles, labels = axes.get_legend_handles_labels()

        if not handles:
            return

        beside: dict[str, Any] = {"loc": "upper left", "bbox_to_anchor": _LEGEND_ANCHOR}
        inside: dict[str, Any] = {"loc": "best"}

        axes.legend(
            handles=handles,
            labels=labels,
            title=title,
            # A handle made of several artists is one swatch, drawn on top of itself.
            handler_map={tuple: HandlerTuple(ndivide=None)},
            **(inside if self._shared_axes is not None else beside),
        )

    def note_missing(self, handles: list[Any], labels: list[str], missing: dict[tuple[str, str], int]) -> None:
        """Add the legend entry that says how many values the figure could not draw.

        What a plot can say beyond that depends on what it draws. A bar has a slot of its
        own to put a cross under, so `BarPlot` marks the categories themselves; a point in
        a cloud or a step of a sweep has no slot, and the count in the key is the whole
        statement there - enough that a filled value is not read as a measured one.

        Parameters
        ----------
        handles : list[Any]
            Legend handles, extended in place.
        labels : list[str]
            Their labels, extended in place alongside *handles*.
        missing : dict[tuple[str, str], int]
            Number of missing values per category and group, as counted by
            :meth:`resolve_missing`.
        """
        from matplotlib.lines import Line2D  # noqa: PLC0415

        if not missing or not self.missing.mark or self.missing.policy == "drop":
            # "drop" leaves them out and says nothing more on the figure; the warning in
            # the log still names them.
            return

        handles.append(Line2D([], [], **MISSING_MARKER))
        labels.append(missing_label(missing))

    def apply_theme(self) -> None:
        """Install the seaborn theme this plot is drawn under, unless it has none.

        The theme is matplotlib's global state rather than a property of one figure, so
        it is installed before the figure is built and left in place afterwards: a
        benchmark themes its plots by handing every one of them the same `Theme`, not by
        each plot putting the previous look back.
        """
        if self.theme is None:
            return

        check_optional_dependency("seaborn")
        from seaborn import set_theme  # noqa: PLC0415

        set_theme(
            context=self.theme.context,
            style=self.theme.seaborn_style,
            font_scale=self.theme.font_scale,
            rc=self.theme.rc or None,
        )

    def apply_grid(self, axes: Axes) -> None:
        """Draw the gridlines the theme asks for, behind everything else on *axes*.

        Parameters
        ----------
        axes : Axes
            The axes the plot was drawn on.
        """
        if self.theme is None:
            return

        if self.theme.grid is None:
            # Said explicitly, so it also takes away the lines a ``grid`` style drew.
            axes.grid(visible=False)
            return

        grid_kwargs: dict[str, Any] = {
            "linestyle": self.theme.grid_linestyle,
            "linewidth": self.theme.grid_linewidth,
            "alpha": self.theme.grid_alpha,
        }
        if self.theme.grid_color is not None:
            grid_kwargs["color"] = self.theme.grid_color

        # Off first, so an axis the theme does not name loses the lines its style drew.
        axes.grid(visible=False)
        axes.grid(visible=True, axis=self.theme.grid, **grid_kwargs)
        # Gridlines are there to be read against, not to be read: behind the marks.
        axes.set_axisbelow(True)

    def setup_figure(self) -> None:
        """Create a matplotlib figure, unless the plot is drawing into a shared axes."""
        check_optional_dependency("matplotlib")
        from matplotlib import pyplot as plt  # noqa: PLC0415

        self.apply_theme()

        if self._shared_axes is not None:
            plt.sca(self._shared_axes)
            return

        plt.figure(figsize=(self.figure.width, self.figure.height), dpi=self.figure.dpi)

    def save_figure(self, save_dir: str) -> list[Path]:
        """Write the current figure to *save_dir* once per configured file format.

        Parameters
        ----------
        save_dir : str
            Directory to save the figure into. Created if it does not exist.

        Returns
        -------
        list[Path]
            Paths that were written successfully.
        """
        check_optional_dependency("matplotlib")
        from matplotlib import pyplot as plt  # noqa: PLC0415

        stem = Path(self.figure.filename)
        if stem.suffix.lstrip(".").lower() in KNOWN_FILE_FORMATS:
            stem = stem.with_suffix("")

        saved = []
        for file_format in self.figure.file_formats:
            normalized = file_format.lstrip(".").lower()
            save_path = Path(save_dir) / f"{stem}.{normalized}"
            save_path.parent.mkdir(parents=True, exist_ok=True)

            if normalized == "pgf":
                if not self._has_texsystem():
                    self.logger.warning(
                        "Skipping '%s': the pgf format needs a LaTeX installation, but '%s' is not on PATH. "
                        "Install one (e.g. 'brew install --cask basictex'), point pgf_texsystem at the engine "
                        "you have, or use a vector format that needs no LaTeX, e.g. file_formats=('pdf',).",
                        save_path.name,
                        self.figure.pgf_texsystem,
                    )
                    continue
                self._configure_pgf()

            try:
                plt.savefig(str(save_path), dpi=self.figure.dpi, bbox_inches="tight")
            except Exception:
                # A failing format (e.g. pgf without LaTeX) must not cost the other formats.
                self.logger.exception("Could not save figure as '%s' to %s", file_format, save_path)
                continue

            saved.append(save_path)
            self.logger.info("Saved figure to %s", save_path)

        return saved

    def _has_texsystem(self) -> bool:
        """Return whether the configured TeX engine is callable on this machine."""
        return shutil.which(self.figure.pgf_texsystem) is not None

    def _configure_pgf(self) -> None:
        """Point the pgf backend at the configured TeX engine and the document fonts."""
        check_optional_dependency("matplotlib")
        import matplotlib as mpl  # noqa: PLC0415

        mpl.rcParams.update(
            {
                "pgf.texsystem": self.figure.pgf_texsystem,
                # Let the LaTeX document set the fonts instead of baking in matplotlib's.
                "pgf.rcfonts": False,
            }
        )

    def finalize_plot(  # noqa: PLR0913, PLR0917
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
        save_dir : str | None, optional
            Directory to save the figure into, by default ``None``.
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

        self.apply_grid(plt.gca())

        if self._shared_axes is not None:
            # One panel of someone else's figure: laying it out, writing it and showing
            # it are decisions about the whole figure, so they are left to its owner.
            return

        plt.tight_layout()

        if save_dir:
            self.save_figure(save_dir)

        if self.figure.show:
            plt.show()

        if save_dir or self.figure.show:
            # Written or shown, so the figure has served its purpose. pyplot keeps every
            # figure alive until it is closed, and a benchmark draws one per plot - past
            # twenty of them matplotlib starts warning about the memory they hold.
            # A figure that was neither written nor shown is left open: closing it would
            # throw the only copy away from a caller who means to read it off the axes.
            plt.close()
