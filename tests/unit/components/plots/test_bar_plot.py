"""Tests for BarPlot generic class."""

from unittest.mock import MagicMock, patch

from matplotlib import pyplot as plt

from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer
from luna_bench.plots.generics.bar_plot import BarPlot
from luna_bench.plots.utils.aggregation_enum import Aggregation


class ConcreteBarPlot(BarPlot):
    """Concrete implementation of BarPlot for testing."""

    def run(self, benchmark_results: BenchmarkResultContainer) -> None:
        """Test implementation for BarPlot."""


class TestBarPlot:
    """Test BarPlot functionality."""

    def teardown_method(self) -> None:
        """Clean up matplotlib figures after each test."""
        plt.close("all")

    @patch("luna_bench.plots.generics.bar_plot.plt.show")
    @patch("luna_bench.plots.generics.bar_plot.sns.barplot")
    def test_create_with_minimal_data(self, mock_barplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create with minimal required data."""
        plot = ConcreteBarPlot()
        rows = [
            {"algorithm": "Algo1", "value": 10},
            {"algorithm": "Algo2", "value": 20},
        ]

        plot.create(
            rows=rows,
            xlabel="Algorithm",
            ylabel="Value",
            title="Test",
        )

        mock_barplot.assert_called_once()
        mock_show.assert_called_once()

    @patch("luna_bench.plots.generics.bar_plot.plt.show")
    @patch("luna_bench.plots.generics.bar_plot.sns.barplot")
    def test_create_with_empty_rows_logs_warning(self, mock_barplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create logs warning when rows is empty."""
        plot = ConcreteBarPlot()

        with patch.object(plot.logger, "warning") as mock_logger:
            plot.create(
                rows=[],
                xlabel="X",
                ylabel="Y",
                title="Test",
            )

            mock_logger.assert_called_once()
            mock_barplot.assert_not_called()
            mock_show.assert_not_called()

    @patch("luna_bench.plots.generics.bar_plot.plt.show")
    @patch("luna_bench.plots.generics.bar_plot.sns.barplot")
    def test_create_with_hue_grouping(self, mock_barplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create with hue parameter for grouped bars."""
        _ = mock_show
        plot = ConcreteBarPlot()
        rows = [
            {"algorithm": "Algo1", "model": "ModelA", "value": 10},
            {"algorithm": "Algo1", "model": "ModelB", "value": 15},
            {"algorithm": "Algo2", "model": "ModelA", "value": 20},
        ]

        plot.create(
            rows=rows,
            xlabel="Algorithm",
            ylabel="Value",
            title="Test",
            hue="model",
            x="algorithm",
            y="value",
        )

        mock_barplot.assert_called_once()
        call_kwargs = mock_barplot.call_args[1]
        assert call_kwargs["hue"] == "model"

    @patch("luna_bench.plots.generics.bar_plot.plt.show")
    @patch("luna_bench.plots.generics.bar_plot.sns.barplot")
    def test_create_with_hline(self, mock_barplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create adds horizontal reference line."""
        _ = mock_barplot, mock_show
        plot = ConcreteBarPlot()
        rows = [{"algorithm": "Algo1", "value": 10}]

        with patch("luna_bench.plots.generics.bar_plot.plt.axhline") as mock_axhline:
            plot.create(
                rows=rows,
                xlabel="X",
                ylabel="Y",
                title="Test",
                hline=5.0,
                hline_label="Reference",
            )

            mock_axhline.assert_called_once()
            call_kwargs = mock_axhline.call_args[1]
            assert call_kwargs["y"] == 5.0
            assert call_kwargs["label"] == "Reference"

    @patch("luna_bench.plots.generics.bar_plot.plt.show")
    @patch("luna_bench.plots.generics.bar_plot.sns.barplot")
    def test_create_with_different_aggregations(self, mock_barplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create with different aggregation strategies."""
        _ = mock_show
        plot = ConcreteBarPlot()
        rows = [
            {"algorithm": "Algo1", "value": 10},
            {"algorithm": "Algo1", "value": 20},
        ]

        for aggregation in [Aggregation.MEAN, Aggregation.MAX, Aggregation.MIN, Aggregation.MEAN_SD]:
            plt.close("all")
            plot.create(
                rows=rows,
                xlabel="X",
                ylabel="Y",
                title="Test",
                aggregation=aggregation,
            )

            call_kwargs = mock_barplot.call_args[1]
            assert call_kwargs["estimator"] == aggregation.value

    @patch("luna_bench.plots.generics.bar_plot.plt.show")
    @patch("luna_bench.plots.generics.bar_plot.sns.barplot")
    def test_create_with_ylim(self, mock_barplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create with y-axis limits."""
        _ = mock_barplot, mock_show
        plot = ConcreteBarPlot()
        rows = [{"algorithm": "Algo1", "value": 10}]

        with patch("luna_bench.plots.generics.bar_plot.plt.ylim") as mock_ylim:
            plot.create(
                rows=rows,
                xlabel="X",
                ylabel="Y",
                title="Test",
                ylim=(0, 100),
            )

            mock_ylim.assert_called_once_with(0, 100)

    @patch("luna_bench.plots.generics.bar_plot.plt.show")
    @patch("luna_bench.plots.generics.bar_plot.sns.barplot")
    def test_create_without_legend(self, mock_barplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create doesn't include legend by default."""
        _ = mock_show
        plot = ConcreteBarPlot()
        rows = [{"algorithm": "Algo1", "value": 10}]

        plot.create(
            rows=rows,
            xlabel="X",
            ylabel="Y",
            title="Test",
            legend=False,
        )

        call_kwargs = mock_barplot.call_args[1]
        assert call_kwargs["legend"] is False

    @patch("luna_bench.plots.generics.bar_plot.plt.show")
    @patch("luna_bench.plots.generics.bar_plot.sns.barplot")
    def test_create_with_legend(self, mock_barplot: MagicMock, mock_show: MagicMock) -> None:
        """Test create with legend enabled."""
        _ = mock_show
        plot = ConcreteBarPlot()
        rows = [{"algorithm": "Algo1", "value": 10}]

        plot.create(
            rows=rows,
            xlabel="X",
            ylabel="Y",
            title="Test",
            legend=True,
        )

        call_kwargs = mock_barplot.call_args[1]
        assert call_kwargs["legend"] is True
