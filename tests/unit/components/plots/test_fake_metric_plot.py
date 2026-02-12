from unittest.mock import MagicMock, patch

from luna_bench.components.metrics.fake_metric import FakeMetric
from luna_bench.components.plots.fake_plot import FakeMetricAveragePerSolverPlot
from luna_bench.components.plots.generics.metrics_plot import MetricsValidationResult
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.entities.metric_entity import MetricEntity

from .conftest import mock_fake_metric_result


class TestFakeMetricAveragePerSolverPlot:
    @patch("luna_bench.components.plots.fake_plot.sns")
    @patch("luna_bench.components.plots.fake_plot.plt")
    def test_run(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        plot = FakeMetricAveragePerSolverPlot()
        data = MetricsValidationResult(
            metrics={
                FakeMetric.registered_id: MetricEntity(
                    name="fake",
                    status=JobStatus.DONE,
                    metric=FakeMetric(),
                    results={
                        ("algo_a", "model_1"): mock_fake_metric_result(
                            model_name="model_1",
                            alg_name="algo_a",
                        ),
                        ("algo_a", "model_2"): mock_fake_metric_result(
                            model_name="model_2",
                            alg_name="algo_a",
                        ),
                        ("algo_b", "model_1"): mock_fake_metric_result(
                            model_name="model_1",
                            alg_name="algo_b",
                        ),
                    },
                )
            }
        )

        plot.run(data)

        mock_sns.barplot.assert_called_once()
        mock_plt.show.assert_called_once()

    @patch("luna_bench.components.plots.fake_plot.sns")
    @patch("luna_bench.components.plots.fake_plot.plt")
    def test_run_skips_none_results(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        plot = FakeMetricAveragePerSolverPlot()
        data = MetricsValidationResult(
            metrics={
                FakeMetric.registered_id: MetricEntity(
                    name="fake",
                    status=JobStatus.DONE,
                    metric=FakeMetric(),
                    results={
                        ("algo_a", "model_1"): mock_fake_metric_result(
                            model_name="model_1",
                            alg_name="algo_a",
                            status="failed",
                        ),
                    },
                )
            }
        )

        plot.run(data)
        mock_sns.barplot.assert_called_once()
        mock_plt.show.assert_called_once()
