"""Shared seaborn-oriented plot infrastructure with figure, axis, and save support."""

from __future__ import annotations

import shutil
from abc import ABC
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import field_validator

from luna_bench.custom import BasePlot
from luna_bench.helpers.optional_dependencies import check_optional_dependency
from luna_bench.logging import BenchLogger

if TYPE_CHECKING:
    from logging import Logger

#: Extensions stripped from ``figure_filename`` before the output format is appended.
KNOWN_FILE_FORMATS = frozenset({"eps", "jpeg", "jpg", "pdf", "pgf", "png", "ps", "svg", "svgz", "tif", "tiff", "webp"})


class SeabornPlot(BasePlot, ABC):
    r"""Base of a seaborn-oriented plot with a shared figure and axis configuration.

    Every attribute below can be set when the plot is constructed, e.g.
    ``AverageRuntimePlot(width=12, file_formats=("pgf", "png"))``.

    Attributes
    ----------
    width : int
        Figure width in inches, by default ``8``.
    height : int
        Figure height in inches, by default ``6``.
    dpi : int
        Resolution of the figure and of the raster files written from it, by default ``100``.
    show : bool
        Open the figure in a window after building it, by default ``True``. Turn this
        off for unattended runs that only write files.
    file_formats : tuple[str, ...]
        Output formats written to ``save_dir``, one file each, by default ``("png",)``.
    pgf_texsystem : str
        TeX engine used for the ``"pgf"`` format, by default ``"pdflatex"``.
    figure_filename : str
        Stem of the written files. The extension comes from *file_formats*.

    Requires
    --------
    Install the 'pre-defined' extra: ``pip install luna-bench[pre-defined]``
    """

    width: int = 8
    """Figure width in inches."""

    height: int = 6
    """Figure height in inches."""

    dpi: int = 100
    """Resolution of the figure and of the raster files written from it."""

    show: bool = True
    """Open the figure in a window after building it. Turn off for unattended runs."""

    file_formats: tuple[str, ...] = ("png",)
    r"""Output formats written to ``save_dir``, one file each.

    A single format may be given as a plain string (``file_formats="pgf"``). ``"pgf"``
    emits a LaTeX-native figure to ``\input{}`` into a document, and needs a working
    LaTeX installation; a format that cannot be written is logged and skipped so the
    remaining ones still land.
    """

    pgf_texsystem: str = "pdflatex"
    """TeX engine used for the ``"pgf"`` format, e.g. ``"pdflatex"`` or ``"lualatex"``."""

    figure_filename: str = "seaborn_plot"
    """Stem of the written files. The extension comes from :attr:`file_formats`."""

    logger: ClassVar[Logger] = BenchLogger.get_logger(__name__)

    @field_validator("file_formats", mode="before")
    @classmethod
    def _accept_single_format(cls, value: Any) -> Any:  # noqa: ANN401
        """Allow a plain string, so ``file_formats="pgf"`` works as well as ``("pgf",)``."""
        return (value,) if isinstance(value, str) else value

    def setup_figure(self) -> None:
        """Create a matplotlib figure."""
        check_optional_dependency("matplotlib")
        from matplotlib import pyplot as plt  # noqa: PLC0415

        plt.figure(figsize=(self.width, self.height), dpi=self.dpi)

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

        stem = Path(self.figure_filename)
        if stem.suffix.lstrip(".").lower() in KNOWN_FILE_FORMATS:
            stem = stem.with_suffix("")

        saved = []
        for file_format in self.file_formats:
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
                        self.pgf_texsystem,
                    )
                    continue
                self._configure_pgf()

            try:
                plt.savefig(str(save_path), dpi=self.dpi, bbox_inches="tight")
            except Exception:
                # A failing format (e.g. pgf without LaTeX) must not cost the other formats.
                self.logger.exception("Could not save figure as '%s' to %s", file_format, save_path)
                continue

            saved.append(save_path)
            self.logger.info("Saved figure to %s", save_path)

        return saved

    def _has_texsystem(self) -> bool:
        """Return whether the configured TeX engine is callable on this machine."""
        return shutil.which(self.pgf_texsystem) is not None

    def _configure_pgf(self) -> None:
        """Point the pgf backend at the configured TeX engine and the document fonts."""
        check_optional_dependency("matplotlib")
        import matplotlib as mpl  # noqa: PLC0415

        mpl.rcParams.update(
            {
                "pgf.texsystem": self.pgf_texsystem,
                # Let the LaTeX document set the fonts instead of baking in matplotlib's.
                "pgf.rcfonts": False,
            }
        )

    def finalize_plot(  # noqa: PLR0913
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

        plt.tight_layout()

        if save_dir:
            self.save_figure(save_dir)

        if self.show:
            plt.show()
