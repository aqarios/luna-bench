"""Tests for ScatterPlot generic class."""

from unittest.mock import MagicMock, patch

from matplotlib import pyplot as plt

from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.plots.generics.scatter_plot import ScatterPlot
from luna_bench.plots.utils.style import AqariosColours


class ConcreteScatterPlot(ScatterPlot):
    """Concrete implementation of ScatterPlot for testing."""

    def run(self, benchmark_results: BenchmarkResultContainer) -> None:
        """Test implementation for ScatterPlot."""


class TestScatterPlot:
    """Test ScatterPlot functionality."""

    def teardown_method(self) -> None:
        """Clean up matplotlib figures after each test."""
        plt.close("all")

    @patch("luna_bench.plots.generics.scatter_plot.plt.show")
    @patch("luna_bench.plots.generics.scatter_plot.scatterplot")
    def test_create_with_minimal_data(self, mock_scatterplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create with minimal required data."""
        plot = ConcreteScatterPlot()
        rows = [
            {"algorithm": "Algo1", "x": 1, "y": 10},
            {"algorithm": "Algo2", "x": 2, "y": 20},
        ]

        plot.create(
            rows=rows,
            xlabel="X Values",
            ylabel="Y Values",
            title="Test Plot",
            hue="algorithm",
        )

        mock_scatterplot.assert_called_once()
        mock_show.assert_called_once()

    @patch("luna_bench.plots.generics.scatter_plot.plt.show")
    @patch("luna_bench.plots.generics.scatter_plot.scatterplot")
    def test_create_with_empty_rows_logs_warning(self, mock_scatterplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create logs warning when rows is empty."""
        plot = ConcreteScatterPlot()

        with patch.object(plot.logger, "warning") as mock_logger:
            plot.create(
                rows=[],
                xlabel="X",
                ylabel="Y",
                title="Test",
                hue="category",
            )

            mock_logger.assert_called_once()
            mock_scatterplot.assert_not_called()
            mock_show.assert_not_called()

    @patch("luna_bench.plots.generics.scatter_plot.plt.show")
    @patch("luna_bench.plots.generics.scatter_plot.scatterplot")
    def test_create_with_hline(self, mock_scatterplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create adds horizontal reference line."""
        _ = mock_scatterplot, mock_show
        plot = ConcreteScatterPlot()
        rows = [
            {"algorithm": "Algo1", "x": 1, "y": 10},
            {"algorithm": "Algo2", "x": 2, "y": 20},
        ]

        with patch("luna_bench.plots.generics.scatter_plot.plt.axhline") as mock_axhline:
            plot.create(
                rows=rows,
                xlabel="X",
                ylabel="Y",
                title="Test",
                hue="algorithm",
                hline=15.0,
                hline_label="Target",
            )

            mock_axhline.assert_called_once()
            call_kwargs = mock_axhline.call_args[1]
            assert call_kwargs["y"] == 15.0
            assert call_kwargs["label"] == "Target"

    @patch("luna_bench.plots.generics.scatter_plot.plt.show")
    @patch("luna_bench.plots.generics.scatter_plot.scatterplot")
    def test_create_without_hline(self, mock_scatterplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create without horizontal line."""
        _ = mock_scatterplot, mock_show
        plot = ConcreteScatterPlot()
        rows = [{"algorithm": "Algo1", "x": 1, "y": 10}]

        with patch("luna_bench.plots.generics.scatter_plot.plt.axhline") as mock_axhline:
            plot.create(
                rows=rows,
                xlabel="X",
                ylabel="Y",
                title="Test",
                hue="algorithm",
                hline=None,
            )

            mock_axhline.assert_not_called()

    @patch("luna_bench.plots.generics.scatter_plot.plt.show")
    @patch("luna_bench.plots.generics.scatter_plot.scatterplot")
    def test_create_with_custom_column_names(self, mock_scatterplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create with custom x and y column names."""
        _ = mock_show
        plot = ConcreteScatterPlot()
        rows = [
            {"solver": "Algo1", "time": 1.5, "quality": 95},
            {"solver": "Algo2", "time": 2.0, "quality": 98},
        ]

        plot.create(
            rows=rows,
            xlabel="Time",
            ylabel="Quality",
            title="Test",
            hue="solver",
            x="time",
            y="quality",
        )

        call_kwargs = mock_scatterplot.call_args[1]
        assert call_kwargs["x"] == "time"
        assert call_kwargs["y"] == "quality"

    @patch("luna_bench.plots.generics.scatter_plot.plt.show")
    @patch("luna_bench.plots.generics.scatter_plot.scatterplot")
    def test_create_with_custom_hline_color(self, mock_scatterplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create with custom horizontal line color."""
        _ = mock_scatterplot, mock_show
        plot = ConcreteScatterPlot()
        rows = [{"algorithm": "Algo1", "x": 1, "y": 10}]

        with patch("luna_bench.plots.generics.scatter_plot.plt.axhline") as mock_axhline:
            plot.create(
                rows=rows,
                xlabel="X",
                ylabel="Y",
                title="Test",
                hue="algorithm",
                hline=5.0,
                hcolor="red",
            )

            call_kwargs = mock_axhline.call_args[1]
            assert call_kwargs["color"] == "red"

    @patch("luna_bench.plots.generics.scatter_plot.plt.show")
    @patch("luna_bench.plots.generics.scatter_plot.scatterplot")
    def test_create_x_rotation_is_zero(self, mock_scatterplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create uses zero x_rotation for scatter plots."""
        _ = mock_scatterplot, mock_show
        plot = ConcreteScatterPlot()
        rows = [{"algorithm": "Algo1", "x": 1, "y": 10}]

        with patch("luna_bench.plots.generics.scatter_plot.plt.xticks") as mock_xticks:
            plot.create(
                rows=rows,
                xlabel="X",
                ylabel="Y",
                title="Test",
                hue="algorithm",
            )

            # x_rotation=0 should not call xticks
            mock_xticks.assert_not_called()

    @patch("luna_bench.plots.generics.scatter_plot.plt.show")
    @patch("luna_bench.plots.generics.scatter_plot.scatterplot")
    def test_create_scatterplot_parameters(self, mock_scatterplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create passes correct parameters to scatterplot."""
        _ = mock_show
        plot = ConcreteScatterPlot()
        rows = [
            {"model": "ModelA", "x": 1, "y": 10},
            {"model": "ModelB", "x": 2, "y": 20},
            {"model": "ModelA", "x": 3, "y": 30},
        ]

        plot.create(
            rows=rows,
            xlabel="X",
            ylabel="Y",
            title="Test",
            hue="model",
        )

        call_kwargs = mock_scatterplot.call_args[1]
        assert call_kwargs["s"] == 60
        assert call_kwargs["alpha"] == 0.8
        assert "palette" in call_kwargs
        assert call_kwargs["hue"] == "model"

    @patch("luna_bench.plots.generics.scatter_plot.plt.show")
    @patch("luna_bench.plots.generics.scatter_plot.scatterplot")
    def test_create_default_hline_color(self, mock_scatterplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create uses success color by default for hline."""
        _ = mock_scatterplot, mock_show
        plot = ConcreteScatterPlot()
        rows = [{"algorithm": "Algo1", "x": 1, "y": 10}]

        with patch("luna_bench.plots.generics.scatter_plot.plt.axhline") as mock_axhline:
            plot.create(
                rows=rows,
                xlabel="X",
                ylabel="Y",
                title="Test",
                hue="algorithm",
                hline=5.0,
            )

            call_kwargs = mock_axhline.call_args[1]
            assert call_kwargs["color"] == AqariosColours.SUCCESS
