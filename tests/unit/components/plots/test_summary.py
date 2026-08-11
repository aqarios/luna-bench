"""Tests for the summary figure holding every plot of a benchmark."""

from collections.abc import Iterator
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from matplotlib import pyplot as plt
from matplotlib.figure import Figure as MatplotlibFigure

from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.plots.generics.seaborn_plot import SeabornPlot
from luna_bench.plots.plot_style import Figure
from luna_bench.plots.summary import _grid, plot_summary


class RecordingPlot(SeabornPlot):
    """A plot that records the axes it was drawn on, and draws a single point."""

    figure_filename: str = "recording"

    def run(self, benchmark_results: BenchmarkResultContainer, save_dir: str | None = None) -> None:
        """Draw a point onto whatever axes is current."""
        _ = benchmark_results, save_dir
        self.setup_figure()
        plt.plot([0], [0])
        self.finalize_plot("x", "y", "title", save_dir=save_dir)


class FailingPlot(SeabornPlot):
    """A plot that cannot be drawn, e.g. because a metric it reads is missing."""

    def run(self, benchmark_results: BenchmarkResultContainer, save_dir: str | None = None) -> None:
        """Fail the way a plot fails on incomplete results."""
        _ = benchmark_results, save_dir
        msg = "no results"
        raise RuntimeError(msg)


def _benchmark(*plots: SeabornPlot, name: str = "bench") -> MagicMock:
    """Return a benchmark whose plot entities carry the given plots."""
    benchmark = MagicMock()
    benchmark.name = name
    benchmark.plots = [MagicMock(plot=plot) for plot in plots]
    return benchmark


@pytest.fixture(autouse=True)
def _close_figures() -> Iterator[None]:
    """Close every figure after each test."""
    yield
    plt.close("all")


@pytest.fixture(autouse=True)
def _empty_results() -> Iterator[MagicMock]:
    """Keep the summary from touching the entity layer for its results."""
    with patch.object(
        BenchmarkResultContainer,
        "from_benchmark",
        return_value=BenchmarkResultContainer(features={}, metrics={}),
    ) as mock_from_benchmark:
        yield mock_from_benchmark


class TestGrid:
    """Test the shape of the grid the panels are laid out in."""

    @pytest.mark.parametrize(
        ("num_plots", "rows", "columns", "expected"),
        [
            (4, None, None, (2, 2)),  # square by default
            (5, None, None, (2, 3)),  # wider than tall
            (1, None, None, (1, 1)),
            (5, None, 3, (2, 3)),  # only columns given
            (5, 2, None, (2, 3)),  # only rows given
            (4, 4, 1, (4, 1)),  # both given
            (3, 4, 2, (4, 2)),  # both given, with room to spare
        ],
    )
    def test_grid_shapes(
        self, num_plots: int, rows: int | None, columns: int | None, expected: tuple[int, int]
    ) -> None:
        """Test the grid always has a cell per plot."""
        assert _grid(num_plots, rows=rows, columns=columns) == expected
        assert expected[0] * expected[1] >= num_plots

    @pytest.mark.parametrize(("rows", "columns"), [(0, 2), (2, 0), (-1, None), (None, -3)])
    def test_a_non_positive_dimension_is_rejected(self, rows: int | None, columns: int | None) -> None:
        """Test a grid has to have at least one row and one column."""
        with pytest.raises(ValueError, match="must be positive"):
            _grid(4, rows=rows, columns=columns)

    def test_a_grid_too_small_for_the_plots_is_rejected(self) -> None:
        """Test silently dropping plots is not an option once a shape was asked for."""
        with pytest.raises(ValueError, match="holds 4 plots"):
            _grid(6, rows=2, columns=2)


class TestPlotSummary:
    """Test the figure the summary builds."""

    def test_every_plot_gets_its_own_panel(self) -> None:
        """Test the plots are drawn side by side rather than into figures of their own."""
        plots = [RecordingPlot(figure=Figure(show=False)) for _ in range(3)]

        plot_summary(_benchmark(*plots), columns=2, show=False)

        figure = plt.gcf()
        used = [axes for axes in figure.axes if axes.get_lines()]
        assert len(used) == len(plots)
        assert len({id(axes) for axes in used}) == len(plots)

    def test_the_spare_panels_are_hidden(self) -> None:
        """Test a grid with room to spare shows no empty axes."""
        plot_summary(_benchmark(RecordingPlot(figure=Figure(show=False))), rows=2, columns=2, show=False)

        assert [axes.axison for axes in plt.gcf().axes] == [True, False, False, False]

    def test_a_plot_that_fails_does_not_cost_the_figure(self) -> None:
        """Test the remaining panels are still drawn, and the failed one is hidden."""
        plot_summary(
            _benchmark(FailingPlot(figure=Figure(show=False)), RecordingPlot(figure=Figure(show=False))),
            columns=2,
            show=False,
        )

        panels = plt.gcf().axes
        assert panels[0].axison is False
        assert panels[1].get_lines()

    def test_the_plots_keep_their_own_figures_afterwards(self) -> None:
        """Test drawing into the summary does not leave the plot redirected."""
        plot = RecordingPlot(figure=Figure(show=False))

        plot_summary(_benchmark(plot), show=False)

        assert plot._shared_axes is None

    def test_a_benchmark_without_plots_draws_nothing(self) -> None:
        """Test an empty benchmark is reported instead of producing a blank page."""
        with patch("luna_bench.plots.summary.logger.warning") as mock_warning:
            assert plot_summary(_benchmark(), show=False) == []

        mock_warning.assert_called_once()

    def test_the_title_defaults_to_the_benchmark_name(self) -> None:
        """Test the page says which benchmark it summarises."""
        plot_summary(_benchmark(RecordingPlot(figure=Figure(show=False)), name="knapsacks"), show=False)

        assert plt.gcf().get_suptitle() == "knapsacks summary"

    def test_the_title_can_be_set(self) -> None:
        """Test the caller can title the page themselves."""
        plot_summary(_benchmark(RecordingPlot(figure=Figure(show=False))), title="Run 3", show=False)

        assert plt.gcf().get_suptitle() == "Run 3"

    def test_the_figure_is_written_once_per_format(self, tmp_path: Path) -> None:
        """Test the grid is saved as a whole, not once per panel."""
        saved = plot_summary(
            _benchmark(RecordingPlot(figure=Figure(show=False))),
            save_dir=str(tmp_path),
            figure_filename="overview.png",
            file_formats=("png", "pdf"),
            show=False,
        )

        assert [path.name for path in saved] == ["overview.png", "overview.pdf"]
        assert all(path.exists() for path in saved)

    def test_a_format_that_cannot_be_written_is_skipped(self, tmp_path: Path) -> None:
        """Test one failing format does not cost the others."""
        with patch.object(MatplotlibFigure, "savefig", side_effect=[ValueError("nope"), None]):
            saved = plot_summary(
                _benchmark(RecordingPlot(figure=Figure(show=False))),
                save_dir=str(tmp_path),
                file_formats=("bogus", "png"),
                show=False,
            )

        assert [path.suffix for path in saved] == [".png"]

    def test_show_opens_the_figure_once(self) -> None:
        """Test the window is opened for the page, not for every panel."""
        with patch.object(plt, "show") as mock_show:
            plot_summary(
                _benchmark(RecordingPlot(figure=Figure(show=True)), RecordingPlot(figure=Figure(show=True))),
                show=True,
            )

        mock_show.assert_called_once()


class TestSummaryFigureLifetime:
    """Test that the summary page does not stay open once it is done with."""

    def test_a_written_page_is_closed(self, tmp_path: Path) -> None:
        """Test the grid, the largest figure of a run, is not left behind."""
        plt.close("all")

        plot_summary(_benchmark(RecordingPlot(figure=Figure(show=False))), save_dir=str(tmp_path), show=False)

        assert plt.get_fignums() == []

    def test_a_page_that_is_only_built_stays_open(self) -> None:
        """Test a caller who neither writes nor shows it can still read the figure."""
        plt.close("all")

        plot_summary(_benchmark(RecordingPlot(figure=Figure(show=False))), show=False)

        assert len(plt.get_fignums()) == 1
