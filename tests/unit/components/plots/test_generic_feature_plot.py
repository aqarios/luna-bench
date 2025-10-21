from typing import ClassVar

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.interfaces.feature_i import IFeature
from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
from luna_bench._internal.user_models.feature_result_usermodel import FeatureResultUserModel
from luna_bench._internal.user_models.feature_usermodel import FeatureUserModel
from luna_bench.components.plots.generics.features_plot import GenericFeaturesPlot
from luna_bench.errors.run_errors.plots_errors.features_missing_error import FeaturesMissingError
from luna_bench.errors.run_errors.plots_errors.metrics_missing_error import MetricsMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from tests.unit.fixtures.mock_components import MockFeature


class _FakePlot(GenericFeaturesPlot):
    metrics_names: ClassVar[set[str]] = {"existing"}
    features_names: ClassVar[set[str]] = {"existing"}

    def run(self) -> None:
        pass


class TestGenericFeaturesPlot:
    @pytest.mark.parametrize(
        ("plot", "feature_name", "exp"),
        [
            (_FakePlot(), "existing", True),
            (_FakePlot(), "non-existing", False),
        ],
    )
    def test_has_feature(
        self,
        plot: GenericFeaturesPlot,
        feature_name: str,
        exp: bool,  # noqa: FBT001
    ) -> None:
        assert plot.has_feature(feature_name) is exp

    def test_add_feature(
        self,
    ) -> None:
        fake_plot = _FakePlot()
        fake_plot.add_feature("existing")

        assert fake_plot.has_feature("existing")
        assert len(fake_plot.features_names) == 1

        fake_plot.add_feature("new")

        assert fake_plot.has_feature("new")
        assert len(fake_plot.features_names) == 2

    @pytest.mark.parametrize(
        ("features", "plot_features", "exp"),
        [
            (
                (
                    (
                        "existing",
                        MockFeature(),
                    ),
                    (
                        "existing2",
                        MockFeature(),
                    ),
                ),
                {"existing", "existing2"},
                Success(
                    {
                        "existing": FeatureUserModel(
                            name="existing",
                            status=JobStatus.CREATED,
                            feature=MockFeature(),
                            results={
                                "": FeatureResultUserModel.model_construct(
                                    processing_time_ms=0,
                                    model_name="test",
                                    status=JobStatus.CREATED,
                                    error=None,
                                    result=None,
                                )
                            },
                        ),
                        "existing2": FeatureUserModel(
                            name="existing2",
                            status=JobStatus.CREATED,
                            feature=MockFeature(),
                            results={
                                "": FeatureResultUserModel.model_construct(
                                    processing_time_ms=0,
                                    model_name="test",
                                    status=JobStatus.CREATED,
                                    error=None,
                                    result=None,
                                )
                            },
                        ),
                    }
                ),
            ),
            (
                (),
                {"existing", "existing2"},
                Failure(FeaturesMissingError(["existing", "existing2"])),
            ),
        ],
    )
    def test_prepare_features(
        self,
        features: tuple[tuple[str, IFeature]],
        plot_features: set[str],
        exp: Result[dict[str, FeatureUserModel], MetricsMissingError | UnknownLunaBenchError],
    ) -> None:
        fake_plot = _FakePlot()
        _FakePlot.features_names = plot_features
        feature_to_prepare = [
            FeatureUserModel(
                name=feature[0],
                status=JobStatus.CREATED,
                feature=feature[1],
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
            for feature in features
        ]

        result = fake_plot._prepare_features(features=feature_to_prepare)
        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    def test_validate_plot(self) -> None:
        fake_plot = _FakePlot()
        _FakePlot.features_names = {"existing"}

        benchmark = BenchmarkUserModel(
            name="test",
            modelset=None,
            features=[],
            algorithms=[],
            metrics=[],
            plots=[],
        )

        result = fake_plot.validate_plot(benchmark)

        assert isinstance(result.failure(), FeaturesMissingError)

        benchmark.features = [
            FeatureUserModel(
                name="existing",
                status=JobStatus.CREATED,
                feature=MockFeature(),
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
        ]
        result = fake_plot.validate_plot(benchmark)

        assert result.unwrap() is None
