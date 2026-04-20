from typing import ClassVar

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench.components.plots.generics.features_plot import FeaturesValidationResult, GenericFeaturesPlot
from luna_bench.entities.benchmark_entity import BenchmarkEntity
from luna_bench.entities.feature_entity import FeatureEntity
from luna_bench.errors.run_errors.plots_errors.features_missing_error import FeaturesMissingError
from luna_bench.errors.run_errors.plots_errors.metrics_missing_error import MetricsMissingError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from tests.unit.components.plots.conftest import mock_feature_entity
from tests.unit.fixtures.mock_components import MockFeature, MockFeatureFailing


class _FakePlot(GenericFeaturesPlot):
    features_ids: ClassVar[set[str]] = {"existing"}

    def run(self, data: FeaturesValidationResult) -> None:
        pass


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
                    mock_feature_entity("existing_name", MockFeature(), ""),
                    mock_feature_entity("existing2_name", MockFeatureFailing(), ""),
                ),
                {
                    MockFeature.registered_id,
                    MockFeatureFailing.registered_id,
                },
                Success(
                    {
                        MockFeature.registered_id: mock_feature_entity("existing_name", MockFeature(), ""),
                        MockFeatureFailing.registered_id: mock_feature_entity(
                            "existing2_name", MockFeatureFailing(), ""
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
        features: tuple[FeatureEntity, ...],
        plot_features: set[str],
        exp: Result[dict[str, FeatureEntity], MetricsMissingError | UnknownLunaBenchError],
    ) -> None:
        fake_plot = _FakePlot()
        _FakePlot.features_ids = plot_features

        result = fake_plot._prepare_features(features=list(features))
        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    def test_validate_plot(self) -> None:
        fake_plot = _FakePlot()
        _FakePlot.features_ids = {MockFeature.registered_id}

        benchmark = BenchmarkEntity(
            name="test",
            modelset=None,
            features=[],
            algorithms=[],
            metrics=[],
            plots=[],
        )

        result = fake_plot.validate_plot(benchmark)

        assert isinstance(result.failure(), FeaturesMissingError)

        benchmark.features = [mock_feature_entity("existing", MockFeature(), "")]
        result = fake_plot.validate_plot(benchmark)

        assert result.unwrap() == FeaturesValidationResult(features={MockFeature.registered_id: benchmark.features[0]})
