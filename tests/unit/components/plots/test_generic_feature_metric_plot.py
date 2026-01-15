from luna_bench.components.plots.generics.features_metrics_plot import (
    FeaturesAndMetricsValidationResult,
    GenericFeaturesMetricsPlot,
)
from luna_bench.entities.benchmark_entity import BenchmarkEntity
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.entities.feature_entity import FeatureEntity
from luna_bench.entities.feature_result_entity import FeatureResultEntity
from luna_bench.entities.metric_entity import MetricEntity
from luna_bench.errors.run_errors.plots_errors.features_missing_error import FeaturesMissingError
from luna_bench.errors.run_errors.plots_errors.metrics_missing_error import MetricsMissingError
from tests.unit.fixtures.mock_components import MockFeature, MockMetric


class _FakePlot(GenericFeaturesMetricsPlot):
    def run(self, data: FeaturesAndMetricsValidationResult) -> None: ...


class TestGenericFeaturesMetricsPlot:
    def test_validate_plot(self) -> None:
        fake_plot = _FakePlot()
        _FakePlot.features_ids = {MockFeature.registered_id}
        _FakePlot.metrics_ids = {MockMetric.registered_id}

        benchmark = BenchmarkEntity(
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
            MetricEntity(
                name="existing",
                status=JobStatus.CREATED,
                metric=MockMetric(),
                results={},
            )
        ]

        result = fake_plot.validate_plot(benchmark)

        assert isinstance(result.failure(), FeaturesMissingError)

        feature = MockFeature()

        feature_user_model = FeatureEntity(
            name="existing",
            status=JobStatus.CREATED,
            feature=feature,
            results={
                "": FeatureResultEntity.model_construct(
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
            features={MockFeature.registered_id: benchmark.features[0]},
            metrics={MockMetric.registered_id: benchmark.metrics[0]},
        )
