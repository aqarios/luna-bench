import typing

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.interfaces.metric_i import IMetric
from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
from luna_bench._internal.user_models.metric_usermodel import MetricUserModel
from luna_bench.components.plots.generics.metrics_plot import GenericMetricsPlot
from luna_bench.errors.run_errors.plots_errors.metrics_missing_error import MetricsMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from tests.unit.fixtures.mock_components import MockMetric


class _FakePlot(GenericMetricsPlot):
    metrics_names: typing.ClassVar[set[str]] = {"existing"}

    def run(self) -> None:
        pass


class TestGenericMetricsPlot:
    @pytest.mark.parametrize(
        ("plot", "metric_name", "exp"),
        [
            (_FakePlot(), "existing", True),
            (_FakePlot(), "non-existing", False),
        ],
    )
    def test_has_metric(
        self,
        plot: GenericMetricsPlot,
        metric_name: str,
        exp: bool,  # noqa: FBT001
    ) -> None:
        assert plot.has_metric(metric_name) is exp

    def test_add_metric(
        self,
    ) -> None:
        fake_plot = _FakePlot()
        fake_plot.add_metric("existing")

        assert fake_plot.has_metric("existing")
        assert len(fake_plot.metrics_names) == 1

        fake_plot.add_metric("new")

        assert fake_plot.has_metric("new")
        assert len(fake_plot.metrics_names) == 2

    @pytest.mark.parametrize(
        ("metrics", "plot_metrics", "exp"),
        [
            (
                (
                    (
                        "existing",
                        MockMetric(),
                    ),
                    (
                        "existing2",
                        MockMetric(),
                    ),
                ),
                {"existing", "existing2"},
                Success(
                    {
                        "existing": MetricUserModel(
                            name="existing",
                            status=JobStatus.CREATED,
                            metric=MockMetric(),
                        ),
                        "existing2": MetricUserModel(
                            name="existing2",
                            status=JobStatus.CREATED,
                            metric=MockMetric(),
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
        metrics: tuple[tuple[str, IMetric]],
        plot_metrics: set[str],
        exp: Result[dict[str, MetricUserModel], MetricsMissingError | UnknownLunaBenchError],
    ) -> None:
        fake_plot = _FakePlot()
        _FakePlot.metrics_names = plot_metrics
        metrics_to_prepare = [
            MetricUserModel(
                name=metric[0],
                status=JobStatus.CREATED,
                metric=metric[1],
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
        _FakePlot.metrics_names = {"existing"}

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
            )
        ]

        result = fake_plot.validate_plot(benchmark)

        assert result.unwrap() is None
