from unittest.mock import MagicMock, patch

from luna_bench.components.features.var_num_feature import VarNumberFeature, VarNumberFeatureResult
from luna_bench.components.metrics.approximation_ratio import ApproximationRatio, ApproximationRatioResult
from luna_bench.components.metrics.feasbility_ratio import FeasibilityRatio, FeasibilityRatioResult
from luna_bench.components.metrics.runtime import Runtime, RuntimeResult
from luna_bench.components.plots.feature_metric_plots import (
    ApproximationRatioVsVarNumberPlot,
    FeasibilityRatioVsVarNumberPlot,
    RuntimeVsVarNumberPlot,
    _build_scatter_dataframe,
)
from luna_bench.components.plots.generics.features_metrics_plot import FeaturesAndMetricsValidationResult
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.entities.feature_entity import FeatureEntity
from luna_bench.entities.feature_result_entity import FeatureResultEntity
from luna_bench.entities.metric_entity import MetricEntity
from luna_bench.entities.metric_result_entity import MetricResultEntity
from luna_bench.types import FeatureResult, MetricResult


def _var_number_entity(*values: tuple[str, int]) -> FeatureEntity:
    results = {}
    for model_name, var_num in values:
        results[model_name] = FeatureResultEntity(
            processing_time_ms=10,
            model_name=model_name,
            status=JobStatus.DONE,
            error=None,
            result=FeatureResult(**VarNumberFeatureResult(var_number=var_num).model_dump()),
        )
    return FeatureEntity(name="var_num", status=JobStatus.DONE, feature=VarNumberFeature(), results=results)


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


def _metric_entity(metric_cls: type, result_cls: type, field: str, *values: tuple[str, str, float]) -> MetricEntity:
    results = {}
    for algo, model, val in values:
        results[(algo, model)] = MetricResultEntity(
            processing_time_ms=10,
            model_name=model,
            algorithm_name=algo,
            status=JobStatus.DONE,
            error=None,
            result=MetricResult(**result_cls(**{field: val}).model_dump()),
        )
    return MetricEntity(name="m", status=JobStatus.DONE, metric=metric_cls(), results=results)


class TestBuildScatterDataframe:
    def test_basic(self) -> None:
        feat = _var_number_entity(("m1", 10), ("m2", 20))
        met = _runtime_entity(("scip", "m1", 1.5), ("scip", "m2", 2.5))
        df = _build_scatter_dataframe(feat, VarNumberFeatureResult, "var_number", met, RuntimeResult, "runtime_seconds")
        assert len(df) == 2
        assert set(df.columns) == {"algorithm", "model", "var_number", "runtime_seconds"}


class TestRuntimeVsVarNumberPlot:
    @patch("luna_bench.components.plots.feature_metric_plots.sns")
    @patch("luna_bench.components.plots.feature_metric_plots.plt")
    def test_run(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        p = RuntimeVsVarNumberPlot()
        data = FeaturesAndMetricsValidationResult(
            features={VarNumberFeature.registered_id: _var_number_entity(("m1", 10), ("m2", 20))},
            metrics={Runtime.registered_id: _runtime_entity(("scip", "m1", 1.5), ("scip", "m2", 2.5))},
        )
        p.run(data)
        mock_sns.scatterplot.assert_called_once()
        mock_plt.show.assert_called_once()


class TestFeasibilityRatioVsVarNumberPlot:
    @patch("luna_bench.components.plots.feature_metric_plots.sns")
    @patch("luna_bench.components.plots.feature_metric_plots.plt")
    def test_run(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:  # noqa: ARG002
        p = FeasibilityRatioVsVarNumberPlot()
        feat = _var_number_entity(("m1", 10))
        met = _metric_entity(FeasibilityRatio, FeasibilityRatioResult, "feasibility_ratio", ("scip", "m1", 0.9))
        p.run(
            FeaturesAndMetricsValidationResult(
                features={VarNumberFeature.registered_id: feat},
                metrics={FeasibilityRatio.registered_id: met},
            )
        )
        mock_sns.scatterplot.assert_called_once()


class TestApproximationRatioVsVarNumberPlot:
    @patch("luna_bench.components.plots.feature_metric_plots.sns")
    @patch("luna_bench.components.plots.feature_metric_plots.plt")
    def test_run(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:  # noqa: ARG002
        p = ApproximationRatioVsVarNumberPlot()
        feat = _var_number_entity(("m1", 10))
        met = _metric_entity(ApproximationRatio, ApproximationRatioResult, "approximation_ratio", ("scip", "m1", 1.1))
        p.run(
            FeaturesAndMetricsValidationResult(
                features={VarNumberFeature.registered_id: feat},
                metrics={ApproximationRatio.registered_id: met},
            )
        )
        mock_sns.scatterplot.assert_called_once()
