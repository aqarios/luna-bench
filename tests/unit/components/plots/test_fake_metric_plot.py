from unittest.mock import MagicMock, patch

from luna_bench.components.plots.fake_plot import FakeMetricAveragePerSolverPlot
from luna_bench.entities.enums.job_status_enum import JobStatus

from .conftest import mock_fake_metric_validation_result


@patch("luna_bench.components.plots.fake_plot.sns")
@patch("luna_bench.components.plots.fake_plot.plt")
class TestFakeMetricAveragePerSolverPlot:
    def test_run(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        plot = FakeMetricAveragePerSolverPlot()
        data = mock_fake_metric_validation_result(
            ("algo_a", "model_1"),
            ("algo_a", "model_2"),
            ("algo_b", "model_1"),
        )

        plot.run(data)

        mock_sns.barplot.assert_called_once()
        mock_plt.show.assert_called_once()

    def test_run_skips_none_results(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        plot = FakeMetricAveragePerSolverPlot()
        data = mock_fake_metric_validation_result(
            ("algo_a", "model_1"),
            status=JobStatus.FAILED,
            error="failed",
        )

        plot.run(data)
        mock_sns.barplot.assert_called_once()
        mock_plt.show.assert_called_once()
