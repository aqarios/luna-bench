from unittest.mock import MagicMock, patch

from luna_bench.components.features.var_num_feature import VarNumberFeature, VarNumberFeatureResult
from luna_bench.components.metrics.approximation_ratio import ApproximationRatio, ApproximationRatioResult
from luna_bench.components.metrics.feasbility_ratio import FeasibilityRatio, FeasibilityRatioResult
from luna_bench.components.metrics.runtime import Runtime, RuntimeResult
from luna_bench.components.plots.feature_metrics_plots.feature_metric_plots import (
    ApproximationRatioVsVarNumberPlot,
    FeasibilityRatioVsVarNumberPlot,
    RuntimeVsVarNumberPlot,
)
from luna_bench.components.plots.generics.features_metrics_plot import FeaturesAndMetricsValidationResult
from luna_bench.components.plots.utils.dataframe_conversion import build_scatter_dataframe
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.entities.feature_entity import FeatureEntity
from luna_bench.entities.metric_entity import MetricEntity

from .conftest import mock_metric_entity, mock_var_entity


class TestBuildScatterDataframe:
    def test_basic(self) -> None:
        feat = mock_var_entity(("m1", 10), ("m2", 20))
        met = mock_metric_entity(
            ("scip", "m1", 1.5),
            ("scip", "m2", 2.5),
            name="runtime",
            metric=Runtime(),
            result_factory=lambda v: RuntimeResult(runtime_seconds=v),
        )
        df = build_scatter_dataframe(feat, VarNumberFeatureResult, "var_number", met, RuntimeResult, "runtime_seconds")
        assert len(df) == 2
        assert set(df.columns) == {"algorithm", "model", "var_number", "runtime_seconds"}


class TestRuntimeVsVarNumberPlot:
    @patch("luna_bench.components.plots.feature_metrics_plots.feature_metric_plots.sns")
    @patch("luna_bench.components.plots.feature_metrics_plots.feature_metric_plots.plt")
    def test_run(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        p = RuntimeVsVarNumberPlot()
        data = FeaturesAndMetricsValidationResult(
            features={VarNumberFeature.registered_id: mock_var_entity(("m1", 10), ("m2", 20))},
            metrics={
                Runtime.registered_id: mock_metric_entity(
                    ("scip", "m1", 1.5),
                    ("scip", "m2", 2.5),
                    name="runtime",
                    metric=Runtime(),
                    result_factory=lambda v: RuntimeResult(runtime_seconds=v),
                )
            },
        )
        p.run(data)
        mock_sns.scatterplot.assert_called_once()
        mock_plt.show.assert_called_once()


class TestFeasibilityRatioVsVarNumberPlot:
    @patch("luna_bench.components.plots.feature_metrics_plots.feature_metric_plots.sns")
    @patch("luna_bench.components.plots.feature_metrics_plots.feature_metric_plots.plt")
    def test_run(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:  # noqa: ARG002
        p = FeasibilityRatioVsVarNumberPlot()
        feat = mock_var_entity(("m1", 10))
        met = mock_metric_entity(
            ("scip", "m1", 0.9),
            name="feasibility",
            metric=FeasibilityRatio(),
            result_factory=lambda v: FeasibilityRatioResult(feasibility_ratio=v),
        )
        p.run(
            FeaturesAndMetricsValidationResult(
                features={VarNumberFeature.registered_id: feat},
                metrics={FeasibilityRatio.registered_id: met},
            )
        )
        mock_sns.scatterplot.assert_called_once()


class TestApproximationRatioVsVarNumberPlot:

    @patch("luna_bench.components.plots.feature_metrics_plots.feature_metric_plots.sns")
    @patch("luna_bench.components.plots.feature_metrics_plots.feature_metric_plots.plt")
    def test_run(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:  # noqa: ARG002
        p = ApproximationRatioVsVarNumberPlot()
        feat = mock_var_entity(("m1", 10))
        met = mock_metric_entity(
            ("scip", "m1", 1.1),
            name="approx",
            metric=ApproximationRatio(),
            result_factory=lambda v: ApproximationRatioResult(approximation_ratio=v),
        )
        p.run(
            FeaturesAndMetricsValidationResult(
                features={VarNumberFeature.registered_id: feat},
                metrics={ApproximationRatio.registered_id: met},
            )
        )
        mock_sns.scatterplot.assert_called_once()


class TestScatterPlotEmptyData:

    @patch("luna_bench.components.plots.feature_metrics_plots.feature_metric_plots.sns")
    @patch("luna_bench.components.plots.feature_metrics_plots.feature_metric_plots.plt")
    def test_run_empty(self, mock_plt: MagicMock, mock_sns: MagicMock) -> None:
        p = RuntimeVsVarNumberPlot()
        feat = FeatureEntity(name="var_num", status=JobStatus.DONE, feature=VarNumberFeature(), results={})
        met = MetricEntity(name="runtime", status=JobStatus.DONE, metric=Runtime(), results={})
        p.run(
            FeaturesAndMetricsValidationResult(
                features={VarNumberFeature.registered_id: feat},
                metrics={Runtime.registered_id: met},
            )
        )
        mock_sns.scatterplot.assert_not_called()
        mock_plt.show.assert_not_called()
