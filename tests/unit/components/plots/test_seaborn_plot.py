"""Tests for SeabornPlot base class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import matplotlib as mpl
from matplotlib import pyplot as plt

from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.plots.generics.seaborn_plot import SeabornPlot
from luna_bench.plots.plot_style import Figure, Theme


class ConcreteSeabornPlot(SeabornPlot):
    """Concrete implementation of SeabornPlot for testing."""

    def run(self, benchmark_results: BenchmarkResultContainer, save_dir: str | None = None) -> None:
        """Test implementation for SeabornPlot."""


class TestSeabornPlot:
    """Test SeabornPlot functionality."""

    def teardown_method(self) -> None:
        """Clean up matplotlib figures after each test."""
        plt.close("all")

    def test_setup_figure_creates_figure_with_defaults(self) -> None:
        """Test that setup_figure creates a figure with correct dimensions."""
        plot = ConcreteSeabornPlot()
        plot.setup_figure()

        fig = plt.gcf()
        assert fig is not None
        assert fig.get_figwidth() == 8
        assert fig.get_figheight() == 6

    def test_setup_figure_with_custom_dimensions(self) -> None:
        """Test setup_figure with custom width and height."""
        plot = ConcreteSeabornPlot()
        plot.figure.width = 12
        plot.figure.height = 8
        plot.setup_figure()

        fig = plt.gcf()
        assert fig.get_figwidth() == 12
        assert fig.get_figheight() == 8

    @patch("luna_bench.plots.generics.seaborn_plot.check_optional_dependency")
    def test_finalize_plot_with_all_parameters(self, mock_check_dep: MagicMock) -> None:
        """Test finalize_plot with all parameters."""
        _ = mock_check_dep
        with patch("matplotlib.pyplot.show") as mock_show:
            plot = ConcreteSeabornPlot()
            plot.setup_figure()

            plot.finalize_plot(
                xlabel="Test X",
                ylabel="Test Y",
                title="Test Title",
                ylim=(0, 100),
                x_rotation=30,
            )

            mock_show.assert_called_once()

    @patch("luna_bench.plots.generics.seaborn_plot.check_optional_dependency")
    def test_finalize_plot_without_show(self, mock_check_dep: MagicMock) -> None:
        """Test finalize_plot respects figure=Figure(show=False)."""
        _ = mock_check_dep
        with patch("matplotlib.pyplot.show") as mock_show:
            plot = ConcreteSeabornPlot()
            plot.figure.show = False
            plot.setup_figure()

            plot.finalize_plot(
                xlabel="X",
                ylabel="Y",
                title="Title",
            )

            mock_show.assert_not_called()

    @patch("luna_bench.plots.generics.seaborn_plot.check_optional_dependency")
    def test_finalize_plot_zero_rotation(self, mock_check_dep: MagicMock) -> None:
        """Test finalize_plot with zero x_rotation doesn't set rotation."""
        _ = mock_check_dep
        with patch("matplotlib.pyplot.show"), patch("matplotlib.pyplot.xticks") as mock_xticks:
            plot = ConcreteSeabornPlot()
            plot.setup_figure()

            plot.finalize_plot(
                xlabel="X",
                ylabel="Y",
                title="Title",
                x_rotation=0,
            )
            mock_xticks.assert_not_called()

    @patch("luna_bench.plots.generics.seaborn_plot.check_optional_dependency")
    def test_finalize_plot_with_ylim(self, mock_check_dep: MagicMock) -> None:
        """Test finalize_plot correctly sets y-axis limits."""
        _ = mock_check_dep
        with patch("matplotlib.pyplot.show"), patch("matplotlib.pyplot.ylim") as mock_ylim:
            plot = ConcreteSeabornPlot()
            plot.setup_figure()

            plot.finalize_plot(
                xlabel="X",
                ylabel="Y",
                title="Title",
                ylim=(10, 50),
            )
            mock_ylim.assert_called_once_with(10, 50)

    @patch("luna_bench.plots.generics.seaborn_plot.check_optional_dependency")
    def test_finalize_plot_without_ylim(self, mock_check_dep: MagicMock) -> None:
        """Test finalize_plot doesn't set ylim when None."""
        _ = mock_check_dep
        with patch("matplotlib.pyplot.show"), patch("matplotlib.pyplot.ylim") as mock_ylim:
            plot = ConcreteSeabornPlot()
            plot.setup_figure()

            plot.finalize_plot(
                xlabel="X",
                ylabel="Y",
                title="Title",
                ylim=None,
            )
            mock_ylim.assert_not_called()

    @patch("luna_bench.plots.generics.seaborn_plot.check_optional_dependency")
    def test_finalize_plot_empty_labels(self, mock_check_dep: MagicMock) -> None:
        """Test finalize_plot with empty string labels."""
        _ = mock_check_dep
        with (
            patch("matplotlib.pyplot.show"),
            patch("matplotlib.pyplot.xlabel") as mock_xlabel,
            patch("matplotlib.pyplot.ylabel") as mock_ylabel,
        ):
            plot = ConcreteSeabornPlot()
            plot.setup_figure()

            plot.finalize_plot(
                xlabel="",
                ylabel="",
                title="Title",
            )
            mock_xlabel.assert_not_called()
            mock_ylabel.assert_not_called()

    def test_defaults_are_correct(self) -> None:
        """Test SeabornPlot has correct default values."""
        plot = ConcreteSeabornPlot()
        assert plot.figure.width == 8
        assert plot.figure.height == 6
        assert plot.figure.dpi == 100
        assert plot.figure.show is True
        assert plot.figure.filename == "figure"
        assert plot.figure.file_formats == ("png",)

    def test_save_figure_writes_one_file_per_format(self, tmp_path: Path) -> None:
        """Test save_figure writes every configured format next to each other."""
        plot = ConcreteSeabornPlot()
        plot.figure.show = False
        plot.figure.filename = "figure.png"
        plot.figure.file_formats = ("png", "svg")
        plot.setup_figure()

        saved = plot.save_figure(str(tmp_path))

        assert saved == [tmp_path / "figure.png", tmp_path / "figure.svg"]
        assert all(path.exists() for path in saved)

    def test_save_figure_keeps_going_when_a_format_fails(self, tmp_path: Path) -> None:
        """Test a format that cannot be written (e.g. pgf without LaTeX) is logged, not raised."""
        plot = ConcreteSeabornPlot()
        plot.figure.show = False
        plot.figure.filename = "figure"
        plot.figure.file_formats = ("broken", "png")
        plot.setup_figure()

        with patch.object(ConcreteSeabornPlot.logger, "exception") as mock_exception:
            saved = plot.save_figure(str(tmp_path))

        mock_exception.assert_called_once()
        assert saved == [tmp_path / "figure.png"]

    def test_save_figure_configures_pgf_backend(self, tmp_path: Path) -> None:
        """Test requesting pgf points matplotlib at the configured TeX engine."""
        plot = ConcreteSeabornPlot()
        plot.figure.show = False
        plot.figure.file_formats = ("pgf",)
        plot.figure.pgf_texsystem = "lualatex"
        plot.setup_figure()

        with (
            patch("matplotlib.pyplot.savefig") as mock_savefig,
            patch("shutil.which", return_value="/usr/bin/lualatex"),
        ):
            plot.save_figure(str(tmp_path))

        assert mpl.rcParams["pgf.texsystem"] == "lualatex"
        assert mpl.rcParams["pgf.rcfonts"] is False
        assert mock_savefig.call_args[0][0] == str(tmp_path / "figure.pgf")

    @patch("luna_bench.plots.generics.seaborn_plot.check_optional_dependency")
    def test_finalize_plot_with_save_dir(self, mock_check_dep: MagicMock) -> None:
        """Test finalize_plot with save_dir saves the figure."""
        _ = mock_check_dep
        with (
            patch("matplotlib.pyplot.show") as mock_show,
            patch("matplotlib.pyplot.savefig") as mock_savefig,
            patch("pathlib.Path.mkdir") as mock_mkdir,
            patch.object(ConcreteSeabornPlot.logger, "info") as mock_logger,
        ):
            plot = ConcreteSeabornPlot()
            plot.setup_figure()

            plot.finalize_plot(
                xlabel="X",
                ylabel="Y",
                title="Test",
                save_dir="/tmp/test_plots",
            )

            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            mock_savefig.assert_called_once()
            mock_logger.assert_called_once()
            mock_show.assert_called_once()

    def test_save_figure_explains_a_missing_tex_installation(self, tmp_path: Path) -> None:
        """Test pgf is skipped with an actionable warning when no TeX engine is installed."""
        plot = ConcreteSeabornPlot()
        plot.figure.show = False
        plot.figure.filename = "figure"
        plot.figure.file_formats = ("pgf", "png")
        plot.setup_figure()

        with (
            patch("shutil.which", return_value=None),
            patch.object(ConcreteSeabornPlot.logger, "warning") as mock_warning,
        ):
            saved = plot.save_figure(str(tmp_path))

        assert saved == [tmp_path / "figure.png"]
        assert "LaTeX" in mock_warning.call_args[0][0]


class TestFigureLifetime:
    """Test that a plot does not leave its figure behind once it is done with it."""

    def teardown_method(self) -> None:
        """Clean up matplotlib figures after each test."""
        plt.close("all")

    def test_a_written_figure_is_closed(self, tmp_path: Path) -> None:
        """Test a benchmark drawing many plots does not pile figures up in memory."""
        plt.close("all")

        for index in range(3):
            plot = ConcreteSeabornPlot(figure=Figure(show=False, filename=f"figure_{index}"))
            plot.setup_figure()
            plot.finalize_plot("X", "Y", "Test", save_dir=str(tmp_path))

        assert plt.get_fignums() == []

    def test_a_shown_figure_is_closed(self) -> None:
        """Test the window having been opened is enough to be done with the figure."""
        plt.close("all")
        plot = ConcreteSeabornPlot(figure=Figure(show=True))
        plot.setup_figure()

        with patch("matplotlib.pyplot.show"):
            plot.finalize_plot("X", "Y", "Test")

        assert plt.get_fignums() == []

    def test_a_figure_that_is_neither_written_nor_shown_stays_open(self) -> None:
        """Test the only copy is not thrown away from a caller who means to read it."""
        plt.close("all")
        plot = ConcreteSeabornPlot(figure=Figure(show=False))
        plot.setup_figure()

        plot.finalize_plot("X", "Y", "Test")

        assert len(plt.get_fignums()) == 1
        assert plt.gca().get_title() == "Test"


class TestTheme:
    """Test the seaborn theme and the gridlines a plot is drawn under."""

    def teardown_method(self) -> None:
        """Clean up matplotlib figures and the global theme after each test."""
        plt.close("all")
        mpl.rcParams.update(mpl.rcParamsDefault)

    def test_a_plot_is_themed_by_default(self) -> None:
        """Test a figure comes with the lines it is meant to be read against."""
        plot = ConcreteSeabornPlot(figure=Figure(show=False))

        assert plot.theme is not None
        assert (plot.theme.seaborn_style, plot.theme.grid) == ("whitegrid", "y")

        plot.setup_figure()
        plot.finalize_plot("X", "Y", "T")

        assert plt.gca().yaxis.get_gridlines()[0].get_visible()

    def test_no_theme_leaves_matplotlib_alone(self) -> None:
        """Test a plot that says it wants none draws the way matplotlib would."""
        plot = ConcreteSeabornPlot(figure=Figure(show=False), theme=None)

        with patch("seaborn.set_theme") as mock_set_theme:
            plot.setup_figure()
        plot.finalize_plot("X", "Y", "T")

        mock_set_theme.assert_not_called()
        assert not plt.gca().yaxis.get_gridlines()[0].get_visible()

    def test_the_theme_is_installed_before_the_figure(self) -> None:
        """Test seaborn is told the style, the context and the scale that were asked for."""
        theme = Theme(seaborn_style="ticks", context="talk", font_scale=1.4, rc={"axes.linewidth": 2.0})

        with patch("seaborn.set_theme") as mock_set_theme:
            ConcreteSeabornPlot(figure=Figure(show=False), theme=theme).setup_figure()

        mock_set_theme.assert_called_once_with(
            context="talk", style="ticks", font_scale=1.4, rc={"axes.linewidth": 2.0}
        )

    def test_the_gridlines_run_off_the_named_axis(self) -> None:
        """Test the value axis gets the lines and the category axis does not."""
        plot = ConcreteSeabornPlot(figure=Figure(show=False), theme=Theme(grid="y", grid_alpha=0.25))
        plot.setup_figure()

        plot.finalize_plot("X", "Y", "T")

        axes = plt.gca()
        assert axes.yaxis.get_gridlines()[0].get_visible()
        assert not axes.xaxis.get_gridlines()[0].get_visible()
        assert axes.yaxis.get_gridlines()[0].get_alpha() == 0.25
        # Behind the bars, so they are read against rather than read.
        assert axes.get_axisbelow()

    def test_no_gridlines_takes_away_the_ones_the_style_drew(self) -> None:
        """Test ``grid=None`` wins over a seaborn style that brings a grid of its own."""
        plot = ConcreteSeabornPlot(figure=Figure(show=False), theme=Theme(seaborn_style="whitegrid", grid=None))
        plot.setup_figure()

        plot.finalize_plot("X", "Y", "T")

        assert not plt.gca().yaxis.get_gridlines()[0].get_visible()
