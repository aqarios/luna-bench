from __future__ import annotations

from typing import TYPE_CHECKING, cast

import pytest

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.registries.arbitrary_data_registry import ArbitraryDataRegistry
from luna_bench.base_components import BaseFeature
from luna_bench.helpers.decorators.feature import feature

if TYPE_CHECKING:
    from luna_model import Model

    from luna_bench._internal.registries import Registry


class TestFeatureFunction:
    """Test the feature_function decorator."""

    @pytest.fixture()
    def registry(self) -> Registry[BaseFeature]:
        return ArbitraryDataRegistry[BaseFeature](kind="xD")

    def test_feature_function_registration(self, registry: Registry[BaseFeature]) -> None:
        """Test that a function decorated with feature_function is registered correctly."""

        @feature(feature_registry=registry)
        def my_test_feature(model: Model) -> int:
            """Docstring."""
            _ = self
            _ = model
            return 42

        # Verify it's a class
        assert isinstance(my_test_feature, type)
        assert issubclass(my_test_feature, BaseFeature)
        assert my_test_feature.__name__ == "my_test_feature"

        # Verify registration in registry

        assert any("my_test_feature" in r_id for r_id in registry.ids())

    def test_feature_function_execution(self) -> None:
        """Test that the wrapped function can be executed."""

        @feature
        def another_test_feature(model: Model) -> int:
            """Docstring."""
            _ = self
            _ = model
            return 123

        # Instantiate and run
        # We use type: ignore because Mypy is confused by the dynamic class
        feature_inst = another_test_feature()
        assert feature_inst.run(cast("Model", None)) == ArbitraryDataDomain.model_construct(result=123)

    def test_feature_function_with_id(self, registry: Registry[BaseFeature]) -> None:
        """Test that feature_function works with a custom ID."""

        @feature(feature_id="custom_id", feature_registry=registry)
        def feature_with_id(model: Model) -> int:
            """Docstring."""
            _ = self
            _ = model
            return 0

        assert "custom_id" in registry.ids()
