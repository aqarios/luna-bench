from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pytest
from luna_model import Model

from luna_bench._internal.registries.arbitrary_data_registry import ArbitraryDataRegistry
from luna_bench.custom import BaseFeature
from luna_bench.custom.decorators.decorator_utilities import DecoratorUtilities
from luna_bench.errors.incompatible_class_error import IncompatibleClassError

if TYPE_CHECKING:
    from luna_bench._internal.registries import Registry


@pytest.fixture()
def registry() -> Registry[BaseFeature]:
    return ArbitraryDataRegistry[BaseFeature](kind="xD")


class TestRegisterClass:
    """Only subclasses of the declared base may be registered."""

    def test_a_class_that_is_not_a_subclass_is_rejected(self, registry: Registry[BaseFeature]) -> None:
        class NotAFeature:
            pass

        with pytest.raises(IncompatibleClassError):
            DecoratorUtilities.register_class(
                NotAFeature,  # type: ignore[arg-type]
                base=BaseFeature,
                registered_class_id="x",
                registry=registry,
            )

    def test_a_non_class_object_is_rejected(self, registry: Registry[BaseFeature]) -> None:
        with pytest.raises(IncompatibleClassError):
            DecoratorUtilities.register_class(
                "not a class",  # type: ignore[arg-type]
                base=BaseFeature,
                registered_class_id="x",
                registry=registry,
            )


class TestValidateSignature:
    """Unresolvable annotations downgrade to a warning rather than failing the decorator."""

    def test_unresolvable_type_hints_are_skipped_with_a_warning(self, caplog: pytest.LogCaptureFixture) -> None:
        def run(model: "DefinitelyNotDefinedAnywhere") -> None:  # type: ignore[name-defined] # noqa: F821, UP037
            _ = model

        with caplog.at_level(logging.WARNING):
            DecoratorUtilities.validate_signature(run, parameter_map={"model": Model})

        assert "Could not get type hints" in caplog.text
