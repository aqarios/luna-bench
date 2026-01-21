from __future__ import annotations

from typing import TYPE_CHECKING, cast

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.interfaces import IFeature
from luna_bench.helpers import feature_function, features

if TYPE_CHECKING:
    from luna_quantum import Model


class TestFeatureFunction:
    """Test the feature_function decorator."""

    def test_feature_function_registration(self) -> None:
        """Test that a function decorated with feature_function is registered correctly."""

        @feature_function
        def my_test_feature(self: IFeature, model: Model) -> int:
            """Docstring."""
            _ = self
            _ = model
            return 42

        # Verify it's a class
        assert isinstance(my_test_feature, type)
        assert issubclass(my_test_feature, IFeature)
        assert my_test_feature.__name__ == "my_test_feature"

        # Verify registration in registry
        registry = features()
        assert any("my_test_feature" in r_id for r_id in registry.ids())

    def test_feature_function_execution(self) -> None:
        """Test that the wrapped function can be executed."""

        @feature_function
        def another_test_feature(self: IFeature, model: Model) -> int:
            """Docstring."""
            _ = self
            _ = model
            return 123

        # Instantiate and run
        # We use type: ignore because Mypy is confused by the dynamic class
        feature_inst = another_test_feature()  # type: ignore[call-arg]
        assert feature_inst.run(cast("Model", None)) == ArbitraryDataDomain.model_construct(result=123)  # type: ignore[arg-type, call-arg]

    def test_feature_function_with_id(self) -> None:
        """Test that feature_function works with a custom ID."""

        @feature_function(feature_id="custom_id")  # type: ignore[misc, call-arg]
        def feature_with_id(self: IFeature, model: Model) -> int:
            """Docstring."""
            _ = self
            _ = model
            return 0

        registry = features()
        assert "custom_id" in registry.ids()
