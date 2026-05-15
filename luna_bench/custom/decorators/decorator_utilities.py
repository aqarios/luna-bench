import inspect
from collections.abc import Callable
from typing import Any, get_type_hints

from luna_quantum import Logging

from luna_bench._internal.registries.protocols import Registry
from luna_bench.custom.base_components.base_feature import BaseFeature
from luna_bench.custom.base_components.base_metric import BaseMetric
from luna_bench.custom.base_components.registerable_component import RegisterableComponent
from luna_bench.errors.decorators.invalid_parameter_type_error import InvalidParameterTypeError
from luna_bench.errors.decorators.invalid_signature_error import InvalidSignatureError
from luna_bench.errors.incompatible_class_error import IncompatibleClassError


class DecoratorUtilities:
    """Utility helpers for the component decorators."""

    _logger = Logging.get_logger(__name__)

    @staticmethod
    def register_class(
        register_class: type[RegisterableComponent],
        *,
        base: type | tuple[type, ...],
        registered_class_id: str | None,
        registry: Registry[Any],
    ) -> None:
        """Register a class in a registry after validating base compatibility.

        Parameters
        ----------
        register_class : type[Any]
            Class to register.
        base : type | tuple[type, ...]
            Required base class or classes the class must inherit from.
        registered_class_id : str | None
            Optional explicit registration identifier.
        registry : Registry[Any]
            Registry where the class is stored.

        Raises
        ------
        IncompatibleClassError
            If the provided class is not a subclass of ``base``.
        """
        if not isinstance(register_class, type) or not issubclass(register_class, base):
            raise IncompatibleClassError(base)
        pid = registered_class_id or f"{register_class.__module__}.{register_class.__qualname__}"

        register_class.registered_id = pid  # We define it here internally.
        # Adding type hint for the registered_id attribute
        registry.register(pid, register_class)

    @staticmethod
    def convert_to_list[T](value: T | list[T] | tuple[T, ...] | None) -> list[T]:
        """Normalize a value into a list.

        Parameters
        ----------
        value : T | list[T] | tuple[T, ...] | None
            Value to normalize.

        Returns
        -------
        list[T]
            Empty list for ``None``, or a list containing the provided value(s).
        """
        if value is None:
            return []
        if isinstance(value, (list, tuple)):
            return list(value)
        return [value]

    @staticmethod
    def validate_signature(func: Callable[..., Any], parameter_map: dict[str, Any]) -> None:
        """Validate that a function has the required parameters and type hints.

        Parameters
        ----------
        func : Callable
            The function to validate.
        parameter_map : dict[str, Any]
            A mapping of parameter names to their expected types.
            Example: {'solution': Solution, 'feature_results': FeatureResults}

        Raises
        ------
        InvalidSignatureError
            If required parameters are missing or have incorrect names.
        InvalidParameterTypeError
            If parameter types do not match expected types when type hints are available.
        """
        sig = inspect.signature(func)
        func_params = list(sig.parameters.keys())
        expected_params = list(parameter_map.keys())

        if func_params != expected_params:
            raise InvalidSignatureError(func.__name__, expected_params, func_params)

        type_namespace = {t.__name__: t for t in parameter_map.values()}
        try:
            type_hints = get_type_hints(func, globalns={**func.__globals__, **type_namespace})
        except NameError:
            DecoratorUtilities._logger.warning(f"Could not get type hints for {func.__name__}. Skipping validation.")
            return

        for param_name, expected_type in parameter_map.items():
            hint_type = type_hints.get(param_name)
            if hint_type is not None and hint_type != expected_type:
                raise InvalidParameterTypeError(param_name, func.__name__, expected_type.__name__, hint_type.__name__)

    @staticmethod
    def split_components(
        components: type[BaseFeature[Any]] | type[BaseMetric[Any]] | list[Any] | tuple[Any, ...] | None,
    ) -> tuple[list[type[BaseFeature[Any]]], list[type[BaseMetric[Any]]]]:
        """Split a mixed collection of components into separate feature and metric lists.

        Parameters
        ----------
        components : type[BaseFeature] | type[BaseMetric] | list | tuple | None
            A single component, list, or tuple of feature/metric types, or None.

        Returns
        -------
        tuple[list[type[BaseFeature[Any]]], list[type[BaseMetric[Any]]]]
            A tuple of (features, metrics) lists.

        Raises
        ------
        TypeError
            If any item is not a ``BaseFeature`` or ``BaseMetric`` subclass.
        """
        items = DecoratorUtilities.convert_to_list(components)
        features: list[type[BaseFeature[Any]]] = []
        metrics: list[type[BaseMetric[Any]]] = []
        for item in items:
            if isinstance(item, type) and issubclass(item, BaseMetric):
                metrics.append(item)
            elif isinstance(item, type) and issubclass(item, BaseFeature):
                features.append(item)
            else:
                msg = f"required_components must contain only BaseFeature or BaseMetric subclasses, got {item!r}"
                raise TypeError(msg)
        return features, metrics
