from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from pydantic import BaseModel, ValidationError

if TYPE_CHECKING:
    from collections.abc import Mapping

    from returns.result import Result

    from luna_bench.errors.registry.already_registerd_id_error import AlreadyRegisteredIdError
    from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
    from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class Registry[T](Protocol):
    def register(self, registered_id: str, cls: type[T]) -> Result[None, AlreadyRegisteredIdError]: ...

    def get_by_id(self, registered_id: str) -> Result[type[T], UnknownIdError]: ...

    def get_by_cls(self, cls: type[T]) -> Result[str, UnknownComponentError]: ...

    def ids(self) -> list[str]: ...

    def classes(self) -> Mapping[str, type[T]]: ...

    def contains(self, registered_id: str) -> bool: ...


class PydanticRegistry[USER_MODEL: BaseModel, DOMAIN_MODEL: BaseModel](Registry[USER_MODEL], Protocol):
    def from_domain_to_user_model(
        self, domain_model: DOMAIN_MODEL
    ) -> Result[USER_MODEL, UnknownIdError | ValidationError]: ...

    def from_user_model_to_domain_model(
        self, user_model: USER_MODEL
    ) -> Result[DOMAIN_MODEL, UnknownComponentError]: ...
