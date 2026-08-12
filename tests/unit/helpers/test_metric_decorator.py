from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast

import pytest

from luna_bench._internal.registries.arbitrary_data_registry import ArbitraryDataRegistry
from luna_bench.custom import BaseFeature, BaseMetric, MetricDirection
from luna_bench.custom.base_results.metric_result import MetricResult
from luna_bench.custom.decorators.metric import metric

if TYPE_CHECKING:
    from luna_model import Model, Solution

    from luna_bench._internal.registries import Registry
    from luna_bench.custom.base_results.feature_result import FeatureResult
    from luna_bench.custom.result_containers.feature_result_container import FeatureResultContainer


class MockFeature(BaseFeature):
    def run(self, model: Model) -> FeatureResult:
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
                feature_results: FeatureResultContainer,
            ) -> MetricResult:
                _ = solution, feature_results
                return MetricResult.model_construct(result=0.95)  # type: ignore[call-arg]

        assert isinstance(TestMetric, type)
        assert issubclass(TestMetric, BaseMetric)
        assert any(expected_in_registry in r_id for r_id in registry.ids())

    def test_metric_preserves_function_metadata(self) -> None:
        @metric
        def documented_metric(
            solution: Solution,
            feature_results: FeatureResultContainer,
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
        return_value: float,
        expected_result: float,
    ) -> None:
        @metric
        def typed_metric(
            solution: Solution,
            feature_results: FeatureResultContainer,
        ) -> float:
            _ = solution, feature_results
            return return_value

        metric_inst = typed_metric()
        result = metric_inst.run(cast("Solution", None), cast("FeatureResultContainer", {}))
        assert result.result == expected_result  # type: ignore[attr-defined]

    def test_metric_returns_metric_result_directly(self) -> None:
        @metric
        def metric_returning_result(
            solution: Solution,
            feature_results: FeatureResultContainer,
        ) -> MetricResult:
            _ = solution, feature_results
            return MetricResult.model_construct(result=0.99)  # type: ignore[call-arg]

        metric_inst = metric_returning_result()
        result = metric_inst.run(cast("Solution", None), cast("FeatureResultContainer", {}))
        assert result.result == 0.99  # type: ignore[attr-defined]

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
        required_features: type[BaseFeature] | list[type[BaseFeature]] | tuple[type[BaseFeature], ...] | None,
        expected_features: list[type[BaseFeature]],
    ) -> None:
        @metric(required_features, metric_registry=registry)
        class FeaturedMetric(BaseMetric):
            def run(
                self,
                solution: Solution,
                feature_results: FeatureResultContainer,
            ) -> MetricResult:
                _ = solution, feature_results
                return MetricResult.model_construct(result=0.5)  # type: ignore[call-arg]

        assert FeaturedMetric.required_features == expected_features

    def test_function_metric_defaults_to_indifferent(self, registry: Registry[BaseMetric]) -> None:
        """A function-based metric declares no direction unless the decorator is given one."""

        @metric(metric_registry=registry)
        def plain_metric(solution: Solution, feature_results: FeatureResultContainer) -> float:
            _ = solution, feature_results
            return 0.5

        assert plain_metric.direction is MetricDirection.INDIFFERENT

    @pytest.mark.parametrize("direction", [MetricDirection.LOWER_IS_BETTER, MetricDirection.HIGHER_IS_BETTER])
    def test_function_metric_direction(self, registry: Registry[BaseMetric], direction: MetricDirection) -> None:
        """A function-based metric has no class body, so the decorator has to carry the direction."""

        @metric(direction=direction, metric_registry=registry)
        def directed_metric(solution: Solution, feature_results: FeatureResultContainer) -> float:
            _ = solution, feature_results
            return 0.5

        assert directed_metric.direction is direction
        assert BaseMetric.direction is MetricDirection.INDIFFERENT

    def test_function_metric_direction_with_features(self, registry: Registry[BaseMetric]) -> None:
        """The direction survives being combined with feature dependencies."""

        @metric(MockFeature, direction=MetricDirection.HIGHER_IS_BETTER, metric_registry=registry)
        def featured_metric(solution: Solution, feature_results: FeatureResultContainer) -> float:
            _ = solution, feature_results
            return 0.5

        assert featured_metric.direction is MetricDirection.HIGHER_IS_BETTER
        assert featured_metric.required_features == [MockFeature]

    def test_class_metric_keeps_its_own_direction(self, registry: Registry[BaseMetric]) -> None:
        """A class declaring its direction keeps it when the decorator passes none."""

        @metric(metric_registry=registry)
        class DirectedMetric(BaseMetric):
            direction: ClassVar[MetricDirection] = MetricDirection.HIGHER_IS_BETTER

            def run(
                self,
                solution: Solution,
                feature_results: FeatureResultContainer,
            ) -> MetricResult:
                _ = solution, feature_results
                return MetricResult.model_construct(result=0.5)  # type: ignore[call-arg]

        assert DirectedMetric.direction is MetricDirection.HIGHER_IS_BETTER

    def test_decorator_direction_overrides_the_class(self, registry: Registry[BaseMetric]) -> None:
        """An explicit decorator direction wins over the one declared on the class."""

        @metric(direction=MetricDirection.LOWER_IS_BETTER, metric_registry=registry)
        class OverriddenMetric(BaseMetric):
            direction: ClassVar[MetricDirection] = MetricDirection.HIGHER_IS_BETTER

            def run(
                self,
                solution: Solution,
                feature_results: FeatureResultContainer,
            ) -> MetricResult:
                _ = solution, feature_results
                return MetricResult.model_construct(result=0.5)  # type: ignore[call-arg]

        assert OverriddenMetric.direction is MetricDirection.LOWER_IS_BETTER
