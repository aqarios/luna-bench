"""Tests for SeabornPlot base class."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import matplotlib as mpl
from matplotlib import pyplot as plt

from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.plots.generics.seaborn_plot import SeabornPlot


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
        plot.width = 12
        plot.height = 8
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
        """Test finalize_plot respects show=False."""
        _ = mock_check_dep
        with patch("matplotlib.pyplot.show") as mock_show:
            plot = ConcreteSeabornPlot()
            plot.show = False
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
        assert plot.width == 8
        assert plot.height == 6
        assert plot.dpi == 100
        assert plot.show is True
        assert plot.figure_filename == "seaborn_plot"
        assert plot.file_formats == ("png",)

    def test_save_figure_writes_one_file_per_format(self, tmp_path: Path) -> None:
        """Test save_figure writes every configured format next to each other."""
        plot = ConcreteSeabornPlot()
        plot.show = False
        plot.figure_filename = "figure.png"
        plot.file_formats = ("png", "svg")
        plot.setup_figure()

        saved = plot.save_figure(str(tmp_path))

        assert saved == [tmp_path / "figure.png", tmp_path / "figure.svg"]
        assert all(path.exists() for path in saved)

    def test_save_figure_keeps_going_when_a_format_fails(self, tmp_path: Path) -> None:
        """Test a format that cannot be written (e.g. pgf without LaTeX) is logged, not raised."""
        plot = ConcreteSeabornPlot()
        plot.show = False
        plot.figure_filename = "figure"
        plot.file_formats = ("broken", "png")
        plot.setup_figure()

        with patch.object(ConcreteSeabornPlot.logger, "exception") as mock_exception:
            saved = plot.save_figure(str(tmp_path))

        mock_exception.assert_called_once()
        assert saved == [tmp_path / "figure.png"]

    def test_save_figure_configures_pgf_backend(self, tmp_path: Path) -> None:
        """Test requesting pgf points matplotlib at the configured TeX engine."""
        plot = ConcreteSeabornPlot()
        plot.show = False
        plot.file_formats = ("pgf",)
        plot.pgf_texsystem = "lualatex"
        plot.setup_figure()

        with (
            patch("matplotlib.pyplot.savefig") as mock_savefig,
            patch("shutil.which", return_value="/usr/bin/lualatex"),
        ):
            plot.save_figure(str(tmp_path))

        assert mpl.rcParams["pgf.texsystem"] == "lualatex"
        assert mpl.rcParams["pgf.rcfonts"] is False
        assert mock_savefig.call_args[0][0] == str(tmp_path / "seaborn_plot.pgf")

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
        plot.show = False
        plot.figure_filename = "figure"
        plot.file_formats = ("pgf", "png")
        plot.setup_figure()

        with (
            patch("shutil.which", return_value=None),
            patch.object(ConcreteSeabornPlot.logger, "warning") as mock_warning,
        ):
            saved = plot.save_figure(str(tmp_path))

        assert saved == [tmp_path / "figure.png"]
        assert "LaTeX" in mock_warning.call_args[0][0]
