from unittest.mock import MagicMock, patch

import pytest

from luna_bench.components.metrics.approximation_ratio import ApproximationRatio, ApproximationRatioResult
from luna_bench.components.metrics.feasbility_ratio import FeasibilityRatio, FeasibilityRatioResult
from luna_bench.components.metrics.runtime import Runtime, RuntimeResult
from luna_bench.components.plots import RuntimePerModelPlot
from luna_bench.components.plots.generics.metrics_plot import MetricsValidationResult
from luna_bench.components.plots.metrics_plots.aggregated_plots import (
    AverageApproximationRatioPlot,
    AverageFeasibilityRatioPlot,
    AverageRuntimePlot,
)
from luna_bench.components.plots.utils.dataframe_conversion import metric_to_dataframe
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.entities.metric_entity import MetricEntity
from luna_bench.entities.metric_result_entity import MetricResultEntity

from .conftest import mock_metric_entity


class TestMetricToDataframe:
    def test_basic(self) -> None:
        entity = mock_metric_entity(
            ("scip", "m1", 1.5),
            ("scip", "m2", 2.5),
            name="runtime",
            metric=Runtime(),
            result_factory=lambda v: RuntimeResult(runtime_seconds=v),
        )
        df = metric_to_dataframe(entity, RuntimeResult, "runtime_seconds")
        assert len(df) == 2
        assert list(df.columns) == ["algorithm", "model", "runtime_seconds"]

    def test_skips_none_results(self) -> None:
        entity = mock_metric_entity(
            name="runtime",
            metric=Runtime(),
            result_factory=lambda v: RuntimeResult(runtime_seconds=v),
        )
        entity.results[("algo", "m1")] = MetricResultEntity(
            processing_time_ms=0,
            model_name="m1",
            algorithm_name="algo",
            status=JobStatus.FAILED,
            error="err",
            result=None,
        )
        df = metric_to_dataframe(entity, RuntimeResult, "runtime_seconds")
        assert len(df) == 0

    def test_skips_inf_values(self) -> None:
        entity = mock_metric_entity(
            ("scip", "m1", float("inf")),
            name="approx",
            metric=ApproximationRatio(),
            result_factory=lambda v: ApproximationRatioResult(approximation_ratio=v),
        )
        df = metric_to_dataframe(entity, ApproximationRatioResult, "approximation_ratio")
        assert len(df) == 0


class TestAverageMetricPlot:
    @pytest.mark.parametrize(
        ("plot_cls", "metric_id", "entity"),
        [
            (
                AverageRuntimePlot,
                Runtime.registered_id,
                mock_metric_entity(
                    ("scip", "m1", 1.5),
                    ("fake", "m1", 0.1),
                    name="runtime",
                    metric=Runtime(),
                    result_factory=lambda v: RuntimeResult(runtime_seconds=v),
                ),
            ),
            (
                AverageFeasibilityRatioPlot,
                FeasibilityRatio.registered_id,
                mock_metric_entity(
                    ("scip", "m1", 1.0),
                    ("scip", "m2", 0.8),
                    name="feasibility",
                    metric=FeasibilityRatio(),
                    result_factory=lambda v: FeasibilityRatioResult(feasibility_ratio=v),
                ),
            ),
            (
                AverageApproximationRatioPlot,
                ApproximationRatio.registered_id,
                mock_metric_entity(
                    ("scip", "m1", 1.0),
                    ("scip", "m2", 1.2),
                    name="approx",
                    metric=ApproximationRatio(),
                    result_factory=lambda v: ApproximationRatioResult(approximation_ratio=v),
                ),
            ),
        ],
    )
    @patch("luna_bench.components.plots.metrics_plots.aggregated_plots.sns")
    @patch("luna_bench.components.plots.metrics_plots.aggregated_plots.plt")
    def test_run(
        self, mock_plt: MagicMock, mock_sns: MagicMock, plot_cls: type, metric_id: str, entity: MetricEntity
    ) -> None:
        mock_plt.gca.return_value.get_legend_handles_labels.return_value = ([], [])
        plot = plot_cls()
        data = MetricsValidationResult(metrics={metric_id: entity})
        plot.run(data)
        mock_sns.barplot.assert_called_once()
        mock_plt.show.assert_called_once()


class TestAverageRuntimePlotEmptyData:
    @patch("luna_bench.components.plots.metrics_plots.aggregated_plots.sns")
    @patch("luna_bench.components.plots.metrics_plots.aggregated_plots.plt")
    def test_run_empty(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        p = AverageRuntimePlot()
        empty = MetricEntity(name="runtime", status=JobStatus.DONE, metric=Runtime(), results={})
        data = MetricsValidationResult(metrics={Runtime.registered_id: empty})
        p.run(data)
        mock_sns.barplot.assert_not_called()
        mock_plt.show.assert_not_called()


@patch("luna_bench.components.plots.metrics_plots.per_model_plots.sns")
@patch("luna_bench.components.plots.metrics_plots.per_model_plots.plt")
class TestRuntimePerModelPlot:
    def test_run(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        plot = RuntimePerModelPlot()
        data = MetricsValidationResult(
            metrics={
                Runtime.registered_id: mock_metric_entity(
                    ("scip", "m1", 1.5),
                    ("scip", "m2", 2.5),
                    ("fake", "m1", 0.1),
                    ("fake", "m2", 0.1),
                    name="runtime",
                    metric=Runtime(),
                    result_factory=lambda v: RuntimeResult(runtime_seconds=v),
                )
            }
        )
        plot.run(data)
        mock_sns.barplot.assert_called_once()
        call_kwargs = mock_sns.barplot.call_args
        assert "hue" in call_kwargs.kwargs
        mock_plt.show.assert_called_once()

    def test_run_empty(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        plot = RuntimePerModelPlot()
        empty = MetricEntity(name="runtime", status=JobStatus.DONE, metric=Runtime(), results={})
        data = MetricsValidationResult(metrics={Runtime.registered_id: empty})
        plot.run(data)
        mock_sns.barplot.assert_not_called()
        mock_plt.show.assert_not_called()
