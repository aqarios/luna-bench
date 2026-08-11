"""Shared seaborn-oriented plot infrastructure with figure, axis, and save support."""

from __future__ import annotations

import shutil
from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, get_args

from pydantic import PrivateAttr, model_validator

from luna_bench.custom import BasePlot
from luna_bench.helpers.optional_dependencies import check_optional_dependency
from luna_bench.logging import BenchLogger
from luna_bench.plots.dimensions import (
    AlgorithmDimension,
    Dimension,
    FeatureDimension,
    ModelDimension,
    ParameterDimension,
)
from luna_bench.plots.plot_style import Figure, OptionBundle, PlotStyle

if TYPE_CHECKING:
    from logging import Logger

    from matplotlib.axes import Axes

    from luna_bench.custom import BenchmarkResultContainer

#: Extensions stripped from ``figure_filename`` before the output format is appended.
KNOWN_FILE_FORMATS = frozenset({"eps", "jpeg", "jpg", "pdf", "pgf", "png", "ps", "svg", "svgz", "tif", "tiff", "webp"})


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

    Requires
    --------
    Install the 'pre-defined' extra: ``pip install luna-bench[pre-defined]``
    """

    figure: Figure = Figure()
    """The figure this plot is drawn on and the files written from it."""

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

        # A style also carries options that are fields of their own, e.g. the aggregation.
        return {key: value for key, value in shared.items() if key not in cls.model_fields or key not in data} | data

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

    def setup_figure(self) -> None:
        """Create a matplotlib figure, unless the plot is drawing into a shared axes."""
        check_optional_dependency("matplotlib")
        from matplotlib import pyplot as plt  # noqa: PLC0415

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
