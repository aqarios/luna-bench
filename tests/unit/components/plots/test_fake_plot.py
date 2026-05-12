"""Tests for FakePlot class."""

from unittest.mock import MagicMock, patch

import pandas as pd

from luna_bench.components.plots.fake_plot import FakePlot


class TestFakePlot:
    """Test FakePlot functionality."""

    def teardown_method(self) -> None:
        """Clean up matplotlib figures after each test."""
        import matplotlib.pyplot as plt

        plt.close("all")

    @patch("luna_bench.components.plots.fake_plot.plt.show")
    @patch("luna_bench.components.plots.fake_plot.sns.barplot")
    @patch("luna_bench.components.plots.fake_plot.plt.figure")
    def test_fake_plot_is_instantiable(
        self, mock_figure: MagicMock, mock_barplot: MagicMock, mock_show: MagicMock
    ) -> None:
        """Test that FakePlot can be instantiated."""
        _ = mock_figure
        _ = mock_barplot
        _ = mock_show
        plot = FakePlot()
        assert plot is not None

    @patch("luna_bench.components.plots.fake_plot.plt.show")
    @patch("luna_bench.components.plots.fake_plot.sns.barplot")
    @patch("luna_bench.components.plots.fake_plot.plt.figure")
    def test_fake_plot_has_run_method(
        self, mock_figure: MagicMock, mock_barplot: MagicMock, mock_show: MagicMock
    ) -> None:
        """Test that FakePlot has a run method."""
        _ = mock_figure
        _ = mock_barplot
        _ = mock_show
        plot = FakePlot()
        assert hasattr(plot, "run")
        assert callable(plot.run)

    @patch("luna_bench.components.plots.fake_plot.plt.show")
    @patch("luna_bench.components.plots.fake_plot.sns.barplot")
    @patch("luna_bench.components.plots.fake_plot.plt.figure")
    def test_fake_plot_run_creates_figure(
        self, mock_figure: MagicMock, mock_barplot: MagicMock, mock_show: MagicMock
    ) -> None:
        """Test that FakePlot.run creates a figure with correct dimensions."""
        _ = mock_barplot
        _ = mock_show
        metric_result = MagicMock()
        metric_result.random_number = 42.0

        metrics_result = MagicMock()
        metrics_result.get_all.return_value = {"metric1": metric_result}

        benchmark_results = MagicMock()
        benchmark_results.get_all_metrics.return_value = [("model1", "algo1", metrics_result)]

        plot = FakePlot()
        plot.run(benchmark_results)

        assert mock_figure.call_count >= 1
        first_call = mock_figure.call_args_list[0]
        assert first_call[1].get("figsize") == (8, 5)

    @patch("luna_bench.components.plots.fake_plot.plt.show")
    @patch("luna_bench.components.plots.fake_plot.sns.barplot")
    @patch("luna_bench.components.plots.fake_plot.plt.figure")
    def test_fake_plot_run_calls_barplot(
        self, mock_figure: MagicMock, mock_barplot: MagicMock, mock_show: MagicMock
    ) -> None:
        """Test that FakePlot.run calls barplot with correct parameters."""
        _ = mock_figure
        _ = mock_show
        metric_result = MagicMock()
        metric_result.random_number = 42.0

        metrics_result = MagicMock()
        metrics_result.get_all.return_value = {"metric1": metric_result}

        benchmark_results = MagicMock()
        benchmark_results.get_all_metrics.return_value = [("model1", "algo1", metrics_result)]

        plot = FakePlot()
        plot.run(benchmark_results)

        mock_barplot.assert_called_once()
        call_kwargs = mock_barplot.call_args[1]
        assert call_kwargs["x"] == "algorithm"
        assert call_kwargs["y"] == "random_number"
        assert call_kwargs["errorbar"] == "sd"
        assert call_kwargs["hue"] == "algorithm"
        assert call_kwargs["legend"] is False

    @patch("luna_bench.components.plots.fake_plot.plt.show")
    @patch("luna_bench.components.plots.fake_plot.sns.barplot")
    @patch("luna_bench.components.plots.fake_plot.plt.figure")
    def test_fake_plot_run_sets_labels_and_title(
        self, mock_figure: MagicMock, mock_barplot: MagicMock, mock_show: MagicMock
    ) -> None:
        """Test that FakePlot.run sets correct labels and title."""
        _ = mock_figure
        _ = mock_barplot
        _ = mock_show
        metric_result = MagicMock()
        metric_result.random_number = 42.0

        metrics_result = MagicMock()
        metrics_result.get_all.return_value = {"metric1": metric_result}

        benchmark_results = MagicMock()
        benchmark_results.get_all_metrics.return_value = [("model1", "algo1", metrics_result)]

        with (
            patch("luna_bench.components.plots.fake_plot.plt.ylabel") as mock_ylabel,
            patch("luna_bench.components.plots.fake_plot.plt.xlabel") as mock_xlabel,
            patch("luna_bench.components.plots.fake_plot.plt.title") as mock_title,
        ):
            plot = FakePlot()
            plot.run(benchmark_results)

            mock_ylabel.assert_called_once_with("Average random_number")
            mock_xlabel.assert_called_once_with("Algorithm")
            mock_title.assert_called_once_with("Average FakeMetric Value per Solver")

    @patch("luna_bench.components.plots.fake_plot.plt.show")
    @patch("luna_bench.components.plots.fake_plot.sns.barplot")
    @patch("luna_bench.components.plots.fake_plot.plt.figure")
    def test_fake_plot_run_rotates_xticks(
        self, mock_figure: MagicMock, mock_barplot: MagicMock, mock_show: MagicMock
    ) -> None:
        """Test that FakePlot.run rotates x-axis ticks by 45 degrees."""
        _ = mock_figure
        _ = mock_barplot
        _ = mock_show
        metric_result = MagicMock()
        metric_result.random_number = 42.0

        metrics_result = MagicMock()
        metrics_result.get_all.return_value = {"metric1": metric_result}

        benchmark_results = MagicMock()
        benchmark_results.get_all_metrics.return_value = [("model1", "algo1", metrics_result)]

        with patch("luna_bench.components.plots.fake_plot.plt.xticks") as mock_xticks:
            plot = FakePlot()
            plot.run(benchmark_results)

            mock_xticks.assert_called_once_with(rotation=45, ha="right")

    @patch("luna_bench.components.plots.fake_plot.plt.show")
    @patch("luna_bench.components.plots.fake_plot.sns.barplot")
    @patch("luna_bench.components.plots.fake_plot.plt.figure")
    def test_fake_plot_run_calls_show(
        self, mock_figure: MagicMock, mock_barplot: MagicMock, mock_show: MagicMock
    ) -> None:
        """Test that FakePlot.run calls plt.show()."""
        _ = mock_figure
        _ = mock_barplot
        metric_result = MagicMock()
        metric_result.random_number = 42.0

        metrics_result = MagicMock()
        metrics_result.get_all.return_value = {"metric1": metric_result}

        benchmark_results = MagicMock()
        benchmark_results.get_all_metrics.return_value = [("model1", "algo1", metrics_result)]

        plot = FakePlot()
        plot.run(benchmark_results)

        mock_show.assert_called_once()

    @patch("luna_bench.components.plots.fake_plot.plt.show")
    @patch("luna_bench.components.plots.fake_plot.sns.barplot")
    @patch("luna_bench.components.plots.fake_plot.plt.figure")
    def test_fake_plot_run_with_multiple_models_and_algorithms(
        self, mock_figure: MagicMock, mock_barplot: MagicMock, mock_show: MagicMock
    ) -> None:
        """Test FakePlot.run with multiple models and algorithms."""
        _ = mock_figure
        _ = mock_show
        metrics_data = []
        for model_idx in range(2):
            for algo_idx in range(2):
                metric_result = MagicMock()
                metric_result.random_number = 10.0 * algo_idx + model_idx

                metrics_result = MagicMock()
                metrics_result.get_all.return_value = {"metric1": metric_result}

                metrics_data.append((f"model{model_idx}", f"algo{algo_idx}", metrics_result))

        benchmark_results = MagicMock()
        benchmark_results.get_all_metrics.return_value = metrics_data

        plot = FakePlot()
        plot.run(benchmark_results)

        mock_barplot.assert_called_once()
        call_args = mock_barplot.call_args
        data = call_args[1]["data"]
        assert isinstance(data, pd.DataFrame)
        assert len(data) == 4  # 2 models * 2 algorithms

    @patch("luna_bench.components.plots.fake_plot.plt.show")
    @patch("luna_bench.components.plots.fake_plot.sns.barplot")
    @patch("luna_bench.components.plots.fake_plot.plt.figure")
    def test_fake_plot_run_dataframe_contains_required_columns(
        self, mock_figure: MagicMock, mock_barplot: MagicMock, mock_show: MagicMock
    ) -> None:
        """Test that FakePlot.run creates DataFrame with required columns."""
        _ = mock_figure
        _ = mock_show
        metric_result = MagicMock()
        metric_result.random_number = 42.0

        metrics_result = MagicMock()
        metrics_result.get_all.return_value = {"metric1": metric_result}

        benchmark_results = MagicMock()
        benchmark_results.get_all_metrics.return_value = [("model1", "algo1", metrics_result)]

        plot = FakePlot()
        plot.run(benchmark_results)

        call_args = mock_barplot.call_args
        data = call_args[1]["data"]
        assert "algorithm" in data.columns
        assert "model" in data.columns
        assert "random_number" in data.columns
        assert "metric_name" in data.columns

    @patch("luna_bench.components.plots.fake_plot.plt.show")
    @patch("luna_bench.components.plots.fake_plot.sns.barplot")
    @patch("luna_bench.components.plots.fake_plot.plt.figure")
    def test_fake_plot_run_algorithm_column_format(
        self, mock_figure: MagicMock, mock_barplot: MagicMock, mock_show: MagicMock
    ) -> None:
        """Test that algorithm column contains model and metric info."""
        _ = mock_figure
        _ = mock_show
        metric_result = MagicMock()
        metric_result.random_number = 42.0

        metrics_result = MagicMock()
        metrics_result.get_all.return_value = {"metric1": metric_result}

        benchmark_results = MagicMock()
        benchmark_results.get_all_metrics.return_value = [("model1", "algo1", metrics_result)]

        plot = FakePlot()
        plot.run(benchmark_results)

        call_args = mock_barplot.call_args
        data = call_args[1]["data"]
        algorithm_col = data["algorithm"].iloc[0]
        assert "algo1" in algorithm_col
        assert "model1" in algorithm_col
        assert "metric1" in algorithm_col

    @patch("luna_bench.components.plots.fake_plot.plt.show")
    @patch("luna_bench.components.plots.fake_plot.sns.barplot")
    @patch("luna_bench.components.plots.fake_plot.plt.figure")
    def test_fake_plot_run_tight_layout_called(
        self, mock_figure: MagicMock, mock_barplot: MagicMock, mock_show: MagicMock
    ) -> None:
        """Test that FakePlot.run calls tight_layout."""
        _ = mock_figure
        _ = mock_barplot
        _ = mock_show
        metric_result = MagicMock()
        metric_result.random_number = 42.0

        metrics_result = MagicMock()
        metrics_result.get_all.return_value = {"metric1": metric_result}

        benchmark_results = MagicMock()
        benchmark_results.get_all_metrics.return_value = [("model1", "algo1", metrics_result)]

        with patch("luna_bench.components.plots.fake_plot.plt.tight_layout") as mock_tight_layout:
            plot = FakePlot()
            plot.run(benchmark_results)

            mock_tight_layout.assert_called_once()

    @patch("luna_bench.components.plots.fake_plot.plt.show")
    @patch("luna_bench.components.plots.fake_plot.sns.barplot")
    @patch("luna_bench.components.plots.fake_plot.plt.figure")
    @patch("luna_bench.components.plots.fake_plot.AqariosColours.palette")
    def test_fake_plot_run_uses_palette(
        self, mock_palette: MagicMock, mock_figure: MagicMock, mock_barplot: MagicMock, mock_show: MagicMock
    ) -> None:
        """Test that FakePlot.run uses AqariosColours palette."""
        _ = mock_figure
        _ = mock_show
        mock_palette.return_value = ["red", "blue"]

        metric_result = MagicMock()
        metric_result.random_number = 42.0

        metrics_result = MagicMock()
        metrics_result.get_all.return_value = {"metric1": metric_result}

        benchmark_results = MagicMock()
        benchmark_results.get_all_metrics.return_value = [("model1", "algo1", metrics_result)]

        plot = FakePlot()
        plot.run(benchmark_results)

        mock_palette.assert_called_once()
        call_kwargs = mock_barplot.call_args[1]
        assert call_kwargs["palette"] is not None
