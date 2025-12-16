from typing import ClassVar

import pytest
from luna_quantum import Model
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
from luna_bench._internal.user_models.feature_result_usermodel import FeatureResultUserModel
from luna_bench._internal.user_models.feature_usermodel import FeatureUserModel
from luna_bench.base_components import BaseFeature
from luna_bench.components.plots.generics.features_plot import FeaturesValidationResult, GenericFeaturesPlot
from luna_bench.errors.run_errors.plots_errors.features_missing_error import FeaturesMissingError
from luna_bench.errors.run_errors.plots_errors.metrics_missing_error import MetricsMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from luna_bench.helpers.decorators import feature
from tests.unit.fixtures.mock_components import MockFeature


class _FakePlot(GenericFeaturesPlot):
    features_ids: ClassVar[set[str]] = {"existing"}

    def run(self, data: FeaturesValidationResult) -> None:
        pass


@feature(feature_id="mock_feature_new")  # type: ignore[arg-type]
class MockFeatureNew(BaseFeature):  # type: ignore[misc]
    def run(self, model: Model) -> ArbitraryDataDomain:  # noqa: ARG002
        return ArbitraryDataDomain.model_construct(solution="xD")  # type: ignore[call-arg] # Fake data


class TestGenericFeaturesPlot:
    @pytest.mark.parametrize(
        ("plot", "feature_id", "exp"),
        [
            (_FakePlot(), "existing", True),
            (_FakePlot(), "non-existing", False),
        ],
    )
    def test_has_feature(
        self,
        plot: GenericFeaturesPlot,
        feature_id: str,
        exp: bool,  # noqa: FBT001
    ) -> None:
        assert plot.has_feature(feature_id) is exp

    def test_add_feature(
        self,
    ) -> None:
        fake_plot = _FakePlot()
        fake_plot.add_feature("existing")

        assert fake_plot.has_feature("existing")
        assert len(fake_plot.features_ids) == 1

        fake_plot.add_feature("new")

        assert fake_plot.has_feature("new")
        assert len(fake_plot.features_ids) == 2

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
                        MockFeatureNew(),
                    ),
                ),
                {
                    MockFeature.registered_id,  # type: ignore[attr-defined]
                    "mock_feature_new",
                },
                Success(
                    {
                        MockFeature.registered_id: FeatureUserModel(  # type: ignore[attr-defined]
                            name="existing_name",
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
                        "mock_feature_new": FeatureUserModel(
                            name="existing2_name",
                            status=JobStatus.CREATED,
                            feature=MockFeatureNew(),
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
        features: tuple[tuple[str, BaseFeature]],
        plot_features: set[str],
        exp: Result[dict[str, FeatureUserModel], MetricsMissingError | UnknownLunaBenchError],
    ) -> None:
        fake_plot = _FakePlot()
        _FakePlot.features_ids = plot_features
        feature_to_prepares = [
            FeatureUserModel(
                name=f"{feature[0]}_name",
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

        result = fake_plot._prepare_features(features=feature_to_prepares)
        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    def test_validate_plot(self) -> None:
        fake_plot = _FakePlot()
        _FakePlot.features_ids = {MockFeature.registered_id}  # type: ignore[attr-defined]

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

        assert result.unwrap() == FeaturesValidationResult(features={MockFeature.registered_id: benchmark.features[0]})  # type: ignore[attr-defined]
