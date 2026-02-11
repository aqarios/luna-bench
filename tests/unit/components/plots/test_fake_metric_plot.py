from unittest.mock import MagicMock, patch

from luna_bench.components.metrics.fake_metric import FakeMetric, FakeMetricResult
from luna_bench.components.plots.fake_plot import FakeMetricAveragePerSolverPlot
from luna_bench.components.plots.generics.metrics_plot import MetricsValidationResult
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.entities.metric_entity import MetricEntity
from luna_bench.entities.metric_result_entity import MetricResultEntity


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
                        ("algo_a", "model_1"): MetricResultEntity(
                            processing_time_ms=10,
                            model_name="model_1",
                            algorithm_name="algo_a",
                            status=JobStatus.DONE,
                            error=None,
                            result=FakeMetricResult(random_number=42),
                        ),
                        ("algo_a", "model_2"): MetricResultEntity(
                            processing_time_ms=10,
                            model_name="model_2",
                            algorithm_name="algo_a",
                            status=JobStatus.DONE,
                            error=None,
                            result=FakeMetricResult(random_number=58),
                        ),
                        ("algo_b", "model_1"): MetricResultEntity(
                            processing_time_ms=10,
                            model_name="model_1",
                            algorithm_name="algo_b",
                            status=JobStatus.DONE,
                            error=None,
                            result=FakeMetricResult(random_number=30),
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
                        ("algo_a", "model_1"): MetricResultEntity(
                            processing_time_ms=10,
                            model_name="model_1",
                            algorithm_name="algo_a",
                            status=JobStatus.FAILED,
                            error="failed",
                            result=None,
                        ),
                    },
                )
            }
        )

        plot.run(data)
        mock_sns.barplot.assert_called_once()
        mock_plt.show.assert_called_once()
