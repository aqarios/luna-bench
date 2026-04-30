from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import pytest

from luna_bench._internal.registries.arbitrary_data_registry import ArbitraryDataRegistry
from luna_bench.base_components import BaseFeature, BaseMetric
from luna_bench.helpers.decorators.metric import metric
from luna_bench.types import MetricResult

if TYPE_CHECKING:
    from luna_model import Solution

    from luna_bench._internal.registries import Registry
    from luna_bench.base_components.data_types.feature_results import FeatureResults


class MockFeature(BaseFeature):
    def run(self, model: Any) -> Any:
        _ = model
        raise NotImplementedError


class TestMetricDecorator:
    @pytest.fixture()
    def registry(self) -> Registry[BaseMetric]:
        return ArbitraryDataRegistry[BaseMetric](kind="metric")

    @pytest.mark.parametrize(
        ("metric_id", "expected_in_registry"),
        [
            (None, "test_metric"),
            ("custom.metric_id", "custom.metric_id"),
        ],
        ids=["default_id", "custom_id"],
    )
    def test_metric_class_registration(
        self,
        registry: Registry[BaseMetric],
        metric_id: str | None,
        expected_in_registry: str,
    ) -> None:

        @metric(metric_id=metric_id, metric_registry=registry)
        class TestMetric(BaseMetric):
            def run(
                self,
                solution: Solution,
                feature_results: FeatureResults,
            ) -> MetricResult:
                _ = solution, feature_results
                return MetricResult.model_construct(result=0.95)

        assert isinstance(TestMetric, type)
        assert issubclass(TestMetric, BaseMetric)
        assert any(expected_in_registry in r_id for r_id in registry.ids())

    def test_metric_preserves_function_metadata(self) -> None:

        @metric
        def documented_metric(
            solution: Solution,
            feature_results: FeatureResults,
        ) -> float:
            """Run, this is the metric documentation."""
            _ = solution, feature_results
            return 0.85

        assert documented_metric.__doc__ == "Run, this is the metric documentation."
        assert documented_metric.__name__ == "documented_metric"

    @pytest.mark.parametrize(
        ("return_value", "expected_result"),
        [
            (0.95, 0.95),
            (42, 42),
            (1.0, 1.0),
        ],
        ids=["float_return", "int_return", "float_one"],
    )
    def test_metric_function_return_types(
        self,
        return_value: Any,
        expected_result: Any,
    ) -> None:

        @metric
        def typed_metric(
            solution: Solution,
            feature_results: FeatureResults,
        ) -> Any:
            _ = solution, feature_results
            return return_value

        metric_inst = typed_metric()
        result = metric_inst.run(cast(Solution, None), cast("FeatureResults", {}))
        assert result.result == expected_result

    def test_metric_returns_metric_result_directly(self) -> None:

        @metric
        def metric_returning_result(
            solution: Solution,
            feature_results: FeatureResults,
        ) -> MetricResult:
            _ = solution, feature_results
            return MetricResult.model_construct(result=0.99)

        metric_inst = metric_returning_result()
        result = metric_inst.run(cast(Solution, None), cast("FeatureResults", {}))
        assert result.result == 0.99

    @pytest.mark.parametrize(
        ("required_features", "expected_features"),
        [
            (None, []),
            (MockFeature, [MockFeature]),
            ([MockFeature], [MockFeature]),
            ((MockFeature,), [MockFeature]),
        ],
        ids=["no_features", "single_feature", "list_features", "tuple_features"],
    )
    def test_metric_required_features(
        self,
        registry: Registry[BaseMetric],
        required_features: Any,
        expected_features: list[type[BaseFeature]],
    ) -> None:

        @metric(required_features=required_features, metric_registry=registry)
        class featured_metric(BaseMetric):
            def run(
                self,
                solution: Solution,
                feature_results: FeatureResults,
            ) -> MetricResult:
                _ = solution, feature_results
                return MetricResult.model_construct(result=0.5)

        assert featured_metric.required_features == expected_features
