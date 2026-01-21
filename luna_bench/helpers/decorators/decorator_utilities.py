from typing import Any

from luna_bench._internal.registries.protocols import Registry
from luna_bench.errors.incompatible_class_error import IncompatibleClassError


class DecoratorUtilities:
    @staticmethod
    def register_class(
        register_class: type[Any],
        *,
        base: type | tuple[type, ...],
        registered_class_id: str | None,
        registry: Registry[Any],
    ) -> None:
        if not isinstance(register_class, type) or not issubclass(register_class, base):
            raise IncompatibleClassError(base)
        pid = registered_class_id or f"{register_class.__module__}.{register_class.__qualname__}"

        register_class._registered_id = pid  # noqa: SLF001 # We define it here internally.
        registry.register(pid, register_class)
