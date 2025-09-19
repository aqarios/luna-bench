from typing import Any

import pytest
from pydantic import BaseModel
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.registries.base_registry import BaseRegistry
from luna_bench.errors.registry.already_registerd_id_error import AlreadyRegisteredIdError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class TestBaseRegistry:
    @pytest.fixture()
    def demo_registry(self) -> BaseRegistry[BaseModel]:
        r = BaseRegistry[BaseModel]("demo")
        r.register("registered", BaseModel)
        return r

    @pytest.mark.parametrize(
        ("registered_id", "cls", "exp"),
        [
            ("base", BaseModel, Success(None)),
            ("registered", BaseModel, Failure(AlreadyRegisteredIdError("demo", "invalid"))),
        ],
    )
    def test_register(
        self,
        cls: type[BaseModel],
        registered_id: str,
        demo_registry: BaseRegistry[BaseModel],
        exp: Result[None, AlreadyRegisteredIdError],
    ) -> None:
        result: Result[None, AlreadyRegisteredIdError] = demo_registry.register(registered_id, cls)
        assert type(result) is type(exp)

        if is_successful(result):
            assert result.unwrap() is exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("registered_id", "exp"),
        [
            ("registered", Success(BaseModel)),
            ("blub", Failure(UnknownIdError("demo", "invalid"))),
        ],
    )
    def test_get_by_id(
        self,
        demo_registry: BaseRegistry[BaseModel],
        registered_id: str,
        exp: Result[type[BaseModel], AlreadyRegisteredIdError],
    ) -> None:
        result: Result[type[BaseModel], UnknownIdError] = demo_registry.get_by_id(registered_id)
        assert is_successful(result) == is_successful(exp)

        if is_successful(result):
            assert result.unwrap() is exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("cls", "exp"),
        [
            (BaseModel, Success("registered")),
            (str, Failure(UnknownComponentError("demo", str))),
        ],
    )
    def test_get_by_cls(
        self, demo_registry: BaseRegistry[BaseModel], cls: type[Any], exp: Result[str, UnknownComponentError]
    ) -> None:
        result: Result[str, UnknownComponentError] = demo_registry.get_by_cls(cls)
        assert type(result) is type(exp)

        if is_successful(result):
            assert result.unwrap() is exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    def test_utility_functions(self, demo_registry: BaseRegistry[BaseModel]) -> None:
        assert demo_registry.ids() == ["registered"]
        assert demo_registry.classes() == {"registered": BaseModel}
        assert demo_registry.contains("registered") is True
        assert demo_registry.contains("blub") is False
