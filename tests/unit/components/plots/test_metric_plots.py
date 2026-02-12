from unittest.mock import MagicMock, patch

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


def _runtime_entity(*values: tuple[str, str, float]) -> MetricEntity:
    results = {}
    for algo, model, runtime in values:
        results[(algo, model)] = MetricResultEntity(
            processing_time_ms=int(runtime * 1000),
            model_name=model,
            algorithm_name=algo,
            status=JobStatus.DONE,
            error=None,
            result=RuntimeResult(runtime_seconds=runtime),
        )
    return MetricEntity(name="runtime", status=JobStatus.DONE, metric=Runtime(), results=results)


def _feasibility_entity(*values: tuple[str, str, float]) -> MetricEntity:
    results = {}
    for algo, model, ratio in values:
        results[(algo, model)] = MetricResultEntity(
            processing_time_ms=10,
            model_name=model,
            algorithm_name=algo,
            status=JobStatus.DONE,
            error=None,
            result=FeasibilityRatioResult(feasibility_ratio=ratio),
        )
    return MetricEntity(name="feasibility", status=JobStatus.DONE, metric=FeasibilityRatio(), results=results)


def _approx_entity(*values: tuple[str, str, float]) -> MetricEntity:
    results = {}
    for algo, model, ar in values:
        results[(algo, model)] = MetricResultEntity(
            processing_time_ms=10,
            model_name=model,
            algorithm_name=algo,
            status=JobStatus.DONE,
            error=None,
            result=ApproximationRatioResult(approximation_ratio=ar),
        )
    return MetricEntity(name="approx", status=JobStatus.DONE, metric=ApproximationRatio(), results=results)


class TestMetricToDataframe:
    def test_basic(self) -> None:
        entity = _runtime_entity(("scip", "m1", 1.5), ("scip", "m2", 2.5))
        df = metric_to_dataframe(entity, RuntimeResult, "runtime_seconds")
        assert len(df) == 2
        assert list(df.columns) == ["algorithm", "model", "runtime_seconds"]

    def test_skips_none_results(self) -> None:
        entity = _runtime_entity()
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
        entity = _approx_entity(("scip", "m1", float("inf")))
        df = metric_to_dataframe(entity, ApproximationRatioResult, "approximation_ratio")
        assert len(df) == 0


class TestAverageRuntimePlot:
    @patch("luna_bench.components.plots.metrics_plots.aggregated_plots.sns")
    @patch("luna_bench.components.plots.metrics_plots.aggregated_plots.plt")
    def test_run(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        mock_plt.gca.return_value.get_legend_handles_labels.return_value = ([], [])
        plot = AverageRuntimePlot()
        data = MetricsValidationResult(
            metrics={Runtime.registered_id: _runtime_entity(("scip", "m1", 1.5), ("fake", "m1", 0.1))}
        )
        plot.run(data)
        mock_sns.barplot.assert_called_once()
        mock_plt.show.assert_called_once()


class TestAverageFeasibilityRatioPlot:
    @patch("luna_bench.components.plots.metrics_plots.aggregated_plots.sns")
    @patch("luna_bench.components.plots.metrics_plots.aggregated_plots.plt")
    def test_run(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        mock_plt.gca.return_value.get_legend_handles_labels.return_value = ([], [])
        plot = AverageFeasibilityRatioPlot()
        data = MetricsValidationResult(
            metrics={FeasibilityRatio.registered_id: _feasibility_entity(("scip", "m1", 1.0), ("scip", "m2", 0.8))}
        )
        plot.run(data)
        mock_sns.barplot.assert_called_once()
        mock_plt.show.assert_called_once()


class TestAverageApproximationRatioPlot:
    @patch("luna_bench.components.plots.metrics_plots.aggregated_plots.sns")
    @patch("luna_bench.components.plots.metrics_plots.aggregated_plots.plt")
    def test_run(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        mock_plt.gca.return_value.get_legend_handles_labels.return_value = ([], [])
        plot = AverageApproximationRatioPlot()
        data = MetricsValidationResult(
            metrics={ApproximationRatio.registered_id: _approx_entity(("scip", "m1", 1.0), ("scip", "m2", 1.2))}
        )
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


class TestRuntimePerModelPlot:
    @patch("luna_bench.components.plots.metrics_plots.per_model_plots.sns")
    @patch("luna_bench.components.plots.metrics_plots.per_model_plots.plt")
    def test_run(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        plot = RuntimePerModelPlot()
        data = MetricsValidationResult(
            metrics={
                Runtime.registered_id: _runtime_entity(
                    ("scip", "m1", 1.5), ("scip", "m2", 2.5), ("fake", "m1", 0.1), ("fake", "m2", 0.1)
                )
            }
        )
        plot.run(data)
        mock_sns.barplot.assert_called_once()
        call_kwargs = mock_sns.barplot.call_args
        assert "hue" in call_kwargs.kwargs
        mock_plt.show.assert_called_once()

    @patch("luna_bench.components.plots.metrics_plots.per_model_plots.sns")
    @patch("luna_bench.components.plots.metrics_plots.per_model_plots.plt")
    def test_run_empty(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        plot = RuntimePerModelPlot()
        empty = MetricEntity(name="runtime", status=JobStatus.DONE, metric=Runtime(), results={})
        data = MetricsValidationResult(metrics={Runtime.registered_id: empty})
        plot.run(data)
        mock_sns.barplot.assert_not_called()
        mock_plt.show.assert_not_called()
