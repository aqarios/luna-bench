from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import pytest
from returns.pipeline import is_successful

from luna_bench._internal.usecases.benchmark.helper.feature_result_builder import FeatureResultBuilder
from luna_bench.base_components import BaseFeature
from luna_bench.entities import BenchmarkEntity, FeatureEntity
from luna_bench.errors.run_errors.run_feature_missing_error import RunFeatureMissingError
from luna_bench.types import FeatureResult
from tests.unit.fixtures.mock_components import MockFeature
from tests.unit.fixtures.mock_entities import make_feature_entity

if TYPE_CHECKING:
    from luna_model import Model


class TestFeatureResultBuilder:
    class MockFeature2(BaseFeature):
        registered_id: ClassVar[str] = "mock_feature_2"

        def run(self, _model: Model) -> FeatureResult:
            return FeatureResult()

    @staticmethod
    def _make_benchmark(features: list[FeatureEntity]) -> BenchmarkEntity:
        return BenchmarkEntity(
            name="test_bench",
            modelset=None,
            features=features,
            algorithms=[],
            metrics=[],
            plots=[],
        )

    @pytest.mark.parametrize(
        "features",
        [
            [],
            [make_feature_entity("feat_a", ("model_1", {}))],
            [make_feature_entity("feat_a", ("model_1", {}), ("model_2", {}))],
            [make_feature_entity("feat_a", ("model_1", {})), make_feature_entity("feat_b", ("model_1", {}))],
            [
                make_feature_entity("feat_a", ("model_1", {}), ("model_2", {})),
                make_feature_entity("feat_b", ("model_1", {}), ("model_2", {})),
            ],
        ],
    )
    def test_init_builds_lookup_map(self, features: list[FeatureEntity]) -> None:
        benchmark = self._make_benchmark(features)
        builder = FeatureResultBuilder(benchmark)

        assert builder.benchmark is benchmark
        assert isinstance(builder._lookup_map, dict)

    def test_results_success(self) -> None:
        feat = make_feature_entity("feat_a", ("model_1", {}))
        builder = FeatureResultBuilder(self._make_benchmark([feat]))
        result = builder.results("model_1", [MockFeature])

        assert is_successful(result)
        assert result.unwrap().allowed == [MockFeature]

    def test_results_missing_model(self) -> None:
        feat = make_feature_entity("feat_a", ("model_1", {}))
        builder = FeatureResultBuilder(self._make_benchmark([feat]))
        result = builder.results("missing", [MockFeature])

        assert not is_successful(result)
        assert isinstance(result.failure(), RunFeatureMissingError)

    def test_results_missing_feature_class(self) -> None:
        feat = make_feature_entity("feat_a", ("model_1", {}))
        builder = FeatureResultBuilder(self._make_benchmark([feat]))
        result = builder.results("model_1", [self.MockFeature2])

        assert not is_successful(result)
        assert isinstance(result.failure(), RunFeatureMissingError)

    def test_results_empty_benchmark(self) -> None:
        builder = FeatureResultBuilder(self._make_benchmark([]))
        result = builder.results("model_1", [MockFeature])

        assert not is_successful(result)

    @pytest.mark.parametrize(("num_features", "num_models"), [(1, 1), (3, 1), (1, 5), (5, 5)])
    def test_lookup_map_size(self, num_features: int, num_models: int) -> None:
        features = [
            make_feature_entity(f"feat_{i}", *[(f"model_{j}", {}) for j in range(num_models)])
            for i in range(num_features)
        ]
        builder = FeatureResultBuilder(self._make_benchmark(features))

        expected = num_models if (num_features > 0 and num_models > 0) else 0
        assert len(builder._lookup_map) == expected
        for inner in builder._lookup_map.values():
            assert len(inner) == num_features

    def test_results_multiple_calls_independent(self) -> None:
        feat = make_feature_entity("feat_a", ("model_1", {}))
        builder = FeatureResultBuilder(self._make_benchmark([feat]))

        r1 = builder.results("model_1", [MockFeature]).unwrap()
        r2 = builder.results("model_1", [MockFeature]).unwrap()

        assert r1 is not r2
        assert r1.allowed == r2.allowed

    @pytest.mark.parametrize(
        ("models", "query", "should_succeed"),
        [
            (["model_1"], "model_1", True),
            (["model_1"], "model_2", False),
            (["model_1", "model_2"], "model_1", True),
            (["model_1", "model_2"], "model_2", True),
            (["model_1", "model_2"], "model_3", False),
        ],
    )
    def test_results_model_availability(self, *, models: list[str], query: str, should_succeed: bool) -> None:
        feat = make_feature_entity("feat_a", *[(m, {}) for m in models])
        builder = FeatureResultBuilder(self._make_benchmark([feat]))
        result = builder.results(query, [MockFeature])

        assert is_successful(result) == should_succeed
