import typing

import pytest
from luna_quantum import Solution
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
from luna_bench._internal.user_models.metric_usermodel import MetricUserModel
from luna_bench.base_components import BaseMetric
from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.components.metrics.fake_metric import FakeMetricResult
from luna_bench.components.plots.generics.metrics_plot import GenericMetricsPlot, MetricsValidationResult
from luna_bench.errors.run_errors.plots_errors.metrics_missing_error import MetricsMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from luna_bench.helpers.decorators import metric
from tests.unit.fixtures.mock_components import MockMetric


class _FakePlot(GenericMetricsPlot):
    metrics_ids: typing.ClassVar[set[str]] = {"test_metric"}

    def run(self, data: MetricsValidationResult) -> None:
        pass


@metric(metric_id="mock_metric_new")  # type: ignore[arg-type]
class MockMetricNew(BaseMetric):  # type: ignore[misc]
    def run(self, solution: Solution, feature_results: FeatureResults) -> FakeMetricResult:
        raise NotImplementedError


class TestGenericMetricsPlot:
    @pytest.mark.parametrize(
        ("plot", "metric_id", "exp"),
        [
            (_FakePlot(), "test_metric", True),
            (_FakePlot(), "non-existing", False),
        ],
    )
    def test_has_metric(
        self,
        plot: GenericMetricsPlot,
        metric_id: str,
        exp: bool,  # noqa: FBT001
    ) -> None:
        assert plot.has_metric(metric_id) is exp

    def test_add_metric(
        self,
    ) -> None:
        fake_plot = _FakePlot()
        fake_plot.add_metric("test_metric")

        assert fake_plot.has_metric("test_metric")
        assert len(fake_plot.metrics_ids) == 1

        fake_plot.add_metric("new")

        assert fake_plot.has_metric("new")
        assert len(fake_plot.metrics_ids) == 2

    @pytest.mark.parametrize(
        ("metrics", "plot_metrics", "exp"),
        [
            (
                (
                    (
                        "existing_name",
                        MockMetric(),
                    ),
                    (
                        "existing2_name",
                        MockMetricNew(),
                    ),
                ),
                {"mock_metric", "mock_metric_new"},
                Success(
                    {
                        "mock_metric": MetricUserModel(
                            name="existing_name",
                            status=JobStatus.CREATED,
                            metric=MockMetric(),
                            results={},
                        ),
                        "mock_metric_new": MetricUserModel(
                            name="existing2_name",
                            status=JobStatus.CREATED,
                            metric=MockMetricNew(),
                            results={},
                        ),
                    }
                ),
            ),
            (
                (),
                {"existing", "existing2"},
                Failure(MetricsMissingError(["existing", "existing2"])),
            ),
        ],
    )
    def test_prepare_metrics(
        self,
        metrics: tuple[tuple[str, BaseMetric]],
        plot_metrics: set[str],
        exp: Result[dict[str, MetricUserModel], MetricsMissingError | UnknownLunaBenchError],
    ) -> None:
        fake_plot = _FakePlot()
        _FakePlot.metrics_ids = plot_metrics
        metrics_to_prepare = [
            MetricUserModel(
                name=metric[0],
                status=JobStatus.CREATED,
                metric=metric[1],
                results={},
            )
            for metric in metrics
        ]

        result = fake_plot._prepare_metrics(metrics=metrics_to_prepare)
        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    def test_validate_plot(self) -> None:
        fake_plot = _FakePlot()
        _FakePlot.metrics_ids = {"mock_metric"}

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
                name="existing_name",
                status=JobStatus.CREATED,
                metric=MockMetric(),
                results={},
            )
        ]

        result = fake_plot.validate_plot(benchmark)

        assert result.unwrap() == MetricsValidationResult(metrics={"mock_metric": benchmark.metrics[0]})
