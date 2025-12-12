from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
from luna_bench._internal.user_models.feature_result_usermodel import FeatureResultUserModel
from luna_bench._internal.user_models.feature_usermodel import FeatureUserModel
from luna_bench._internal.user_models.metric_usermodel import MetricUserModel
from luna_bench.components.plots.generics.features_metrics_plot import (
    FeaturesAndMetricsValidationResult,
    GenericFeaturesMetricsPlot,
)
from luna_bench.errors.run_errors.plots_errors.features_missing_error import FeaturesMissingError
from luna_bench.errors.run_errors.plots_errors.metrics_missing_error import MetricsMissingError
from tests.unit.fixtures.mock_components import MockFeature, MockMetric


class _FakePlot(GenericFeaturesMetricsPlot):
    def run(self, data: FeaturesAndMetricsValidationResult) -> None: ...


class TestGenericFeaturesMetricsPlot:
    def test_validate_plot(self) -> None:
        fake_plot = _FakePlot()
        _FakePlot.features_ids = {MockFeature.registered_id}  # type: ignore[attr-defined]
        _FakePlot.metrics_ids = {MockMetric.registered_id}  # type: ignore[attr-defined]

        benchmark = BenchmarkUserModel(
            name="test",
            modelset=None,
            features=[],
            algorithms=[],
            metrics=[],
            plots=[],
        )

        result = fake_plot.validate_plot(benchmark)

        assert isinstance(result.failure(), MetricsMissingError)

        benchmark.metrics = [
            MetricUserModel(
                name="existing",
                status=JobStatus.CREATED,
                metric=MockMetric(),
                results={},
            )
        ]

        result = fake_plot.validate_plot(benchmark)

        assert isinstance(result.failure(), FeaturesMissingError)

        feature = MockFeature()

        feature_user_model = FeatureUserModel(
            name="existing",
            status=JobStatus.CREATED,
            feature=feature,
            results={
                "": FeatureResultUserModel.model_construct(
                    processing_time_ms=0,
                    model_name="test",
                    status=JobStatus.CREATED,
                    error=None,
                    result=None,
                )
            },
        )

        benchmark.features = [feature_user_model]
        result = fake_plot.validate_plot(benchmark)

        assert result.unwrap() == FeaturesAndMetricsValidationResult(
            features={MockFeature.registered_id: benchmark.features[0]},  # type: ignore[attr-defined]
            metrics={MockMetric.registered_id: benchmark.metrics[0]},  # type: ignore[attr-defined]
        )
