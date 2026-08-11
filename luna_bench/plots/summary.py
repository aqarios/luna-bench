"""One figure holding every plot of a benchmark, as a grid of subplots."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.helpers.optional_dependencies import check_optional_dependency
from luna_bench.logging import BenchLogger
from luna_bench.plots.generics.seaborn_plot import KNOWN_FILE_FORMATS, SeabornPlot

if TYPE_CHECKING:
    from pathlib import Path

    from luna_bench.entities import BenchmarkEntity

logger = BenchLogger.get_logger(__name__)

#: Size of one panel in inches, before the grid is scaled up.
DEFAULT_PANEL_SIZE = (7.0, 5.0)

#: Height in inches kept free above the panels for the title of the page.
TITLE_BAND_INCHES = 0.5


def plot_summary(  # noqa: PLR0913
    benchmark: BenchmarkEntity,
    *,
    columns: int | None = None,
    rows: int | None = None,
    save_dir: str | None = None,
    figure_filename: str = "summary",
    file_formats: tuple[str, ...] | str = ("png",),
    panel_size: tuple[float, float] = DEFAULT_PANEL_SIZE,
    dpi: int = 100,
    show: bool = True,
    title: str | None = None,
) -> list[Path]:
    """Draw every plot of a benchmark into one figure, one panel each.

    The individual plots keep their own configuration - their labels, colours and
    reference lines - but not their figure: they are redirected onto a panel of the grid,
    which is then written once as a whole. Useful as the single page that says how a
    benchmark went, next to the per-plot files.

    Unlike ``Benchmark.run_plots``, this needs no plot to declare what it requires: it
    hands every plot all results the benchmark has, and a plot that cannot draw with them
    is logged and left out instead of stopping the figure.

    Parameters
    ----------
    benchmark : BenchmarkEntity
        The benchmark whose plots and results are drawn. Run it first; plots of a
        benchmark without results have nothing to show.
    columns : int | None, optional
        Number of columns of the grid. By default derived from *rows*, or from the
        number of plots so the grid stays roughly square.
    rows : int | None, optional
        Number of rows of the grid. By default as many as *columns* needs.
    save_dir : str | None, optional
        Directory to write the figure into, by default ``None``, which only shows it.
    figure_filename : str, optional
        Stem of the written files, by default ``"summary"``.
    file_formats : tuple[str, ...] | str, optional
        Output formats written to *save_dir*, one file each, by default ``("png",)``.
    panel_size : tuple[float, float], optional
        Width and height of a single panel in inches, by default ``(7.0, 5.0)``.
    dpi : int, optional
        Resolution of the figure and of the raster files written from it, by default ``100``.
    show : bool, optional
        Open the figure in a window once it is built, by default ``True``.
    title : str | None, optional
        Title above the grid, by default the name of the benchmark.

    Returns
    -------
    list[Path]
        The files that were written, empty when *save_dir* is ``None`` or the benchmark
        has no plot that could be drawn.

    Examples
    --------
    >>> bench.run()
    >>> plot_summary(bench, columns=3, save_dir="plots", show=False)

    Raises
    ------
    ValueError
        If *rows* or *columns* is not positive, or if the grid they ask for has fewer
        cells than the benchmark has plots.
    """
    check_optional_dependency("matplotlib")
    from matplotlib import pyplot as plt  # noqa: PLC0415

    plots = [entity.plot for entity in benchmark.plots if isinstance(entity.plot, SeabornPlot)]
    if not plots:
        logger.warning("Benchmark '%s' has no plot that can be drawn into a summary.", benchmark.name)
        return []

    grid_rows, grid_columns = _grid(len(plots), rows=rows, columns=columns)

    figure, axes = plt.subplots(
        grid_rows,
        grid_columns,
        figsize=(grid_columns * panel_size[0], grid_rows * panel_size[1]),
        dpi=dpi,
        squeeze=False,
    )
    panels = [axes[row][column] for row in range(grid_rows) for column in range(grid_columns)]

    benchmark_results = BenchmarkResultContainer.from_benchmark(benchmark)
    drawn = 0
    for plot, panel in zip(plots, panels, strict=False):
        try:
            plot.draw_into(panel, benchmark_results)
        except Exception:
            # One plot that cannot be drawn - a missing metric, say - must not cost the
            # whole page.
            logger.exception("Could not draw %s into the summary", type(plot).__name__)
            panel.set_axis_off()
            continue
        drawn += 1

    for panel in panels[len(plots) :]:
        panel.set_axis_off()

    figure.suptitle(title if title is not None else f"{benchmark.name} summary", fontsize="x-large")
    # Reserve a fixed band for the title rather than a fixed share: on a tall grid a
    # share would leave a gap, on a short one it would let the panels run into the title.
    title_band = TITLE_BAND_INCHES / (grid_rows * panel_size[1])
    figure.tight_layout(rect=(0.0, 0.0, 1.0, 1.0 - title_band))

    saved = _save(figure, save_dir, figure_filename, file_formats, dpi) if save_dir else []

    if show:
        plt.show()

    if saved or show:
        # Same rule as a single plot: a page that was written or shown is done with, and
        # a grid of panels is the last figure worth keeping open by accident.
        plt.close(figure)

    logger.info("Summary drawn with %s of %s plots", drawn, len(plots))
    return saved


def _grid(num_plots: int, *, rows: int | None, columns: int | None) -> tuple[int, int]:
    """Return the ``(rows, columns)`` of the grid the panels are laid out in.

    Parameters
    ----------
    num_plots : int
        Number of panels to fit.
    rows : int | None
        Requested number of rows, or ``None`` to derive it.
    columns : int | None
        Requested number of columns, or ``None`` to derive it.

    Returns
    -------
    tuple[int, int]
        Rows and columns, with at least one cell per plot.

    Raises
    ------
    ValueError
        If a requested dimension is not positive, or if both are given and their product
        cannot hold every plot.
    """
    for name, value in (("rows", rows), ("columns", columns)):
        if value is not None and value < 1:
            msg = f"{name} must be positive, got {value}"
            raise ValueError(msg)

    if rows is not None and columns is not None:
        if rows * columns < num_plots:
            msg = f"A {rows}x{columns} grid holds {rows * columns} plots, but the benchmark has {num_plots}"
            raise ValueError(msg)
        return rows, columns

    if columns is not None:
        return math.ceil(num_plots / columns), columns

    if rows is not None:
        return rows, math.ceil(num_plots / rows)

    # Neither was asked for: keep the page roughly square.
    columns = math.ceil(math.sqrt(num_plots))
    return math.ceil(num_plots / columns), columns


def _save(
    figure: Any,  # noqa: ANN401
    save_dir: str,
    figure_filename: str,
    file_formats: tuple[str, ...] | str,
    dpi: int,
) -> list[Path]:
    """Write the summary figure once per requested format.

    Parameters
    ----------
    figure : Any
        The matplotlib figure holding the grid.
    save_dir : str
        Directory to write into. Created if it does not exist.
    figure_filename : str
        Stem of the written files.
    file_formats : tuple[str, ...] | str
        Output formats, one file each.
    dpi : int
        Resolution of the raster files.

    Returns
    -------
    list[Path]
        The files that were written.
    """
    from pathlib import Path  # noqa: PLC0415

    formats = (file_formats,) if isinstance(file_formats, str) else file_formats

    stem = Path(figure_filename)
    if stem.suffix.lstrip(".").lower() in KNOWN_FILE_FORMATS:
        stem = stem.with_suffix("")

    saved: list[Path] = []
    for file_format in formats:
        save_path = Path(save_dir) / f"{stem}.{file_format.lstrip('.').lower()}"
        save_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            figure.savefig(str(save_path), dpi=dpi, bbox_inches="tight")
        except Exception:
            # A failing format must not cost the other formats.
            logger.exception("Could not save the summary as '%s' to %s", file_format, save_path)
            continue

        saved.append(save_path)
        logger.info("Saved summary to %s", save_path)

    return saved
