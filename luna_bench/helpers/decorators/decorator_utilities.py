import inspect
from collections.abc import Callable
from typing import Any, get_type_hints

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

        register_class.registered_id = pid  # We define it here internally.
        registry.register(pid, register_class)

    @staticmethod
    def _convert_to_list[T](value: T | list[T] | tuple[T, ...] | None) -> list[T]:
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return list(value)
        return [value]

    @staticmethod
    def validate_signature(func: Callable, parameter_map: dict[str, Any]) -> None:
        """
        Validate that a function has the required parameters with correct types.

        Parameters
        ----------
        func : Callable
            The function to validate.
        parameter_map : dict[str, Any]
            A mapping of parameter names to their expected types.
            Example: {'solution': Solution, 'feature_results': FeatureResults}

        Raises
        ------
        ValueError
            If required parameters are missing or have incorrect names.
        TypeError
            If parameter types don't match the expected types (when type hints are present).
        """
        sig = inspect.signature(func)
        func_params = list(sig.parameters.keys())
        expected_params = list(parameter_map.keys())

        if func_params != expected_params:
            raise ValueError(f"Function '{func.__name__}' must have parameters {expected_params}, got {func_params}")

        type_hints = get_type_hints(func)
        for param_name, expected_type in parameter_map.items():
            hint_type = type_hints.get(param_name)
            if hint_type is not None and hint_type != expected_type:
                raise TypeError(
                    f"Parameter '{param_name}' in '{func.__name__}' must be of type "
                    f"{expected_type.__name__}, got {hint_type.__name__}"
                )
