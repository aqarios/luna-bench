from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

import pytest

from luna_bench._internal.registries.arbitrary_data_registry import ArbitraryDataRegistry
from luna_bench.base_components import BaseFeature
from luna_bench.helpers.decorators.feature import feature
from luna_bench.types import FeatureResult

if TYPE_CHECKING:
    from luna_model import Model

    from luna_bench._internal.registries import Registry


class TestFeatureDecorator:
    @pytest.fixture()
    def registry(self) -> Registry[BaseFeature]:
        return ArbitraryDataRegistry[BaseFeature](kind="xD")

    @pytest.mark.parametrize(
        ("feature_id", "expected_in_registry"),
        [
            (None, "test_feature"),
            ("custom_id", "custom_id"),
        ],
        ids=["default_id", "custom_id"],
    )
    def test_feature_class_registration(
        self,
        registry: Registry[BaseFeature],
        feature_id: str | None,
        expected_in_registry: str,
    ) -> None:
        @feature(feature_id=feature_id, feature_registry=registry)
        class TestFeature(BaseFeature):
            def run(self, model: Model) -> FeatureResult:
                _ = model
                return FeatureResult.model_construct(result=42)  # type: ignore[call-arg]

        assert isinstance(TestFeature, type)
        assert issubclass(TestFeature, BaseFeature)
        assert any(expected_in_registry in r_id for r_id in registry.ids())

    def test_feature_function_registration(self, registry: Registry[BaseFeature]) -> None:
        @feature(feature_registry=registry)
        def my_test_feature(model: Model) -> int:
            _ = model
            return 42

        assert isinstance(my_test_feature, type)
        assert issubclass(my_test_feature, BaseFeature)
        assert any("my_test_feature" in r_id for r_id in registry.ids())

    def test_feature_function_execution(self) -> None:
        @feature
        def another_test_feature(model: Model) -> int:
            _ = model
            return 123

        feature_inst = another_test_feature()
        result = feature_inst.run(cast("Model", None))
        assert result.result == 123  # type: ignore[attr-defined]

    def test_feature_function_with_custom_id(self, registry: Registry[BaseFeature]) -> None:
        @feature(feature_id="custom_id", feature_registry=registry)
        def feature_with_id(model: Model) -> int:
            _ = model
            return 0

        assert "custom_id" in registry.ids()

    @pytest.mark.parametrize(
        ("return_value", "expected_result"),
        [
            (42, 42),
            ({"key": "value"}, {"key": "value"}),
            ("string_result", "string_result"),
        ],
        ids=["int_return", "dict_return", "string_return"],
    )
    def test_feature_function_return_types(
        self,
        return_value: int | dict[str, Any] | str,
        expected_result: int | dict[str, Any] | str,
    ) -> None:
        @feature
        def typed_feature(model: Model) -> int | dict[str, Any] | str:
            _ = model
            return return_value

        feature_inst = typed_feature()
        result = feature_inst.run(cast("Model", None))
        assert result.result == expected_result  # type: ignore[attr-defined]

    def test_feature_preserves_function_metadata(self) -> None:
        @feature
        def documented_feature(model: Model) -> int:
            """Run, this is the feature documentation."""
            _ = model
            return 0

        assert documented_feature.__doc__ == "Run, this is the feature documentation."
        assert documented_feature.__name__ == "documented_feature"

    def test_feature_returns_feature_result_directly(self) -> None:
        @feature
        def feature_returning_result(model: Model) -> FeatureResult:
            _ = model
            return FeatureResult.model_construct(result=99)  # type: ignore[call-arg]

        feature_inst = feature_returning_result()
        result = feature_inst.run(cast("Model", None))
        assert result.result == 99  # type: ignore[attr-defined]
