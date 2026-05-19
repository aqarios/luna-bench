"""Tests for SeabornPlot base class."""

from unittest.mock import MagicMock, patch

from matplotlib import pyplot as plt

from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.plots.generics.seaborn_plot import SeabornPlot


class ConcreteSeabornPlot(SeabornPlot):
    """Concrete implementation of SeabornPlot for testing."""

    def run(self, benchmark_results: BenchmarkResultContainer) -> None:
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

    @patch("luna_bench.plots.generics.seaborn_plot.plt.show")
    def test_finalize_plot_with_all_parameters(self, mock_show: MagicMock) -> None:
        """Test finalize_plot with all parameters."""
        _ = mock_show
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

    @patch("luna_bench.plots.generics.seaborn_plot.plt.show")
    def test_finalize_plot_without_show(self, mock_show: MagicMock) -> None:
        """Test finalize_plot respects show=False."""
        plot = ConcreteSeabornPlot()
        plot.show = False
        plot.setup_figure()

        plot.finalize_plot(
            xlabel="X",
            ylabel="Y",
            title="Title",
        )

        mock_show.assert_not_called()

    @patch("luna_bench.plots.generics.seaborn_plot.plt.show")
    def test_finalize_plot_zero_rotation(self, mock_show: MagicMock) -> None:
        """Test finalize_plot with zero x_rotation doesn't set rotation."""
        _ = mock_show
        plot = ConcreteSeabornPlot()
        plot.setup_figure()

        with patch("luna_bench.plots.generics.seaborn_plot.plt.xticks") as mock_xticks:
            plot.finalize_plot(
                xlabel="X",
                ylabel="Y",
                title="Title",
                x_rotation=0,
            )
            mock_xticks.assert_not_called()

    @patch("luna_bench.plots.generics.seaborn_plot.plt.show")
    def test_finalize_plot_with_ylim(self, mock_show: MagicMock) -> None:
        """Test finalize_plot correctly sets y-axis limits."""
        _ = mock_show
        plot = ConcreteSeabornPlot()
        plot.setup_figure()

        with patch("luna_bench.plots.generics.seaborn_plot.plt.ylim") as mock_ylim:
            plot.finalize_plot(
                xlabel="X",
                ylabel="Y",
                title="Title",
                ylim=(10, 50),
            )
            mock_ylim.assert_called_once_with(10, 50)

    @patch("luna_bench.plots.generics.seaborn_plot.plt.show")
    def test_finalize_plot_without_ylim(self, mock_show: MagicMock) -> None:
        """Test finalize_plot doesn't set ylim when None."""
        _ = mock_show
        plot = ConcreteSeabornPlot()
        plot.setup_figure()

        with patch("luna_bench.plots.generics.seaborn_plot.plt.ylim") as mock_ylim:
            plot.finalize_plot(
                xlabel="X",
                ylabel="Y",
                title="Title",
                ylim=None,
            )
            mock_ylim.assert_not_called()

    @patch("luna_bench.plots.generics.seaborn_plot.plt.show")
    def test_finalize_plot_empty_labels(self, mock_show: MagicMock) -> None:
        """Test finalize_plot with empty string labels."""
        _ = mock_show
        plot = ConcreteSeabornPlot()
        plot.setup_figure()

        with (
            patch("luna_bench.plots.generics.seaborn_plot.plt.xlabel") as mock_xlabel,
            patch("luna_bench.plots.generics.seaborn_plot.plt.ylabel") as mock_ylabel,
        ):
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
