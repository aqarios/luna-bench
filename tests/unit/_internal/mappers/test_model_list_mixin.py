from typing import Any
from unittest.mock import MagicMock

from returns.result import Failure

from luna_bench._internal.mappers.mixins.model_list_mixin import ModelListMixin
from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class _FailingMapper(ModelListMixin[Any, Any]):
    def to_user_model(self, domain: object) -> Failure[UnknownIdError]:  # noqa: ARG002
        return Failure(UnknownIdError("test", "missing"))


class TestModelListMixin:
    def test_to_user_model_list_propagates_failure(self) -> None:
        mapper = _FailingMapper()
        result = mapper.to_user_model_list([MagicMock()])

        assert isinstance(result, Failure)
        assert isinstance(result.failure(), UnknownIdError)
