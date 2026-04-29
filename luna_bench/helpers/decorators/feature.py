import functools
from collections.abc import Callable
from typing import Any, overload

from dependency_injector.wiring import Provide, inject
from luna_model import Model
from pydantic import BaseModel

from luna_bench._internal.registries.protocols import Registry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench.base_components import BaseFeature
from luna_bench.types import FeatureResult

from .decorator_utilities import DecoratorUtilities


@overload
def feature[T: BaseFeature[Any]](
    _cls: type[T],
    *,
    feature_id: str | None = None,
    feature_registry: Registry[BaseFeature] = Provide[RegistryContainer.feature_registry],
) -> type[T]: ...


@overload
def feature[T: BaseFeature[Any]](
    _cls: Callable[[Model], FeatureResult | BaseModel | object],
    *,
    feature_id: str | None = None,
    feature_registry: Registry[BaseFeature] = Provide[RegistryContainer.feature_registry],
) -> type[BaseFeature[FeatureResult]]: ...


@overload
def feature[T: BaseFeature[Any]](
    _cls: None = None,
    *,
    feature_id: str | None = None,
    feature_registry: Registry[BaseFeature] = Provide[RegistryContainer.feature_registry],
) -> Callable[
    [type[T] | Callable[[Model], FeatureResult | BaseModel | object]], type[BaseFeature[FeatureResult]] | type[T]
]: ...


@inject
def feature[T: BaseFeature[Any]](
    _cls: type[T] | Callable[[Model], FeatureResult | BaseModel | object] | None = None,
    *,
    feature_id: str | None = None,
    feature_registry: Registry[BaseFeature] = Provide[RegistryContainer.feature_registry],
) -> (
    Callable[
        [type[T] | Callable[[Model], FeatureResult | BaseModel | object]], type[BaseFeature[FeatureResult]] | type[T]
    ]
    | type[BaseFeature[FeatureResult]]
    | type[T]
):
    """
    Register a class or function as a feature.

    The decorated class must be a subclass of the ``BaseFeature`` protocol, or a decorated
    function will be automatically wrapped as a ``BaseFeature`` subclass.

    Parameters
    ----------
    _cls : type[T], optional
        The class to be decorated. If None, returns a decorator function.
    feature_id : str | None, optional
        Set a custom ID for the feature. If not provided, the ID will be generated automatically
        from the module and class/function name. It's recommended to not set this parameter.
    feature_registry : Registry[BaseFeature], injected
        The registry where the feature will be registered. Injected by dependency container.

    Returns
    -------
    Callable[[type[T]], type[T]] | type[T]
        Either the decorated class/function or a decorator function.

    Examples
    --------
    Decorate a class as a feature:

    >>> from luna_bench.base_components import BaseFeature
    >>> from luna_model import Model
    >>> from pydantic import BaseModel
    >>>
    >>> @feature
    ... class MyFeature(BaseFeature):
    ...     def run(self, model: Model) -> BaseModel:
    ...         # Extract and return feature data
    ...         return {"feature_value": 42}

    Decorate a function as a feature:

    >>> @feature
    ... def image_dimensions(model: Model) -> dict:
    ...     # Extract image dimensions from model
    ...     return {"width": 640, "height": 480}

    Use a custom feature ID:

    >>> @feature(feature_id="custom.image_dimensions")
    ... def image_dims(model: Model) -> dict:
    ...     return {"width": 640, "height": 480}

    """

    def _feature_class(cls: type[T], pid: str | None = None) -> type[T]:
        if pid is None:
            pid = feature_id or f"{cls.__module__}.{cls.__qualname__}"
        DecoratorUtilities.register_class(cls, base=BaseFeature, registered_class_id=pid, registry=feature_registry)
        return cls

    def _feature_function[RETURN_TYPE: FeatureResult](
        func: Callable[[Model], RETURN_TYPE | BaseModel | object],
    ) -> type[BaseFeature[FeatureResult]]:
        class_name = func.__name__

        DecoratorUtilities.validate_signature(
            func,
            parameter_map={
                "model": Model,
            },
        )

        @functools.wraps(func)
        def run(self: BaseFeature[RETURN_TYPE], model: Model) -> RETURN_TYPE:
            _ = self
            result = func(model)
            if not isinstance(result, FeatureResult):
                return FeatureResult.model_construct(result=result)  # type: ignore[call-arg, return-value]
            return result  # type: ignore[return-value]

        # Create the dynamic class
        dynamic_class = type(
            class_name,
            (BaseFeature,),
            {
                "run": run,
                "__module__": func.__module__,
                "__doc__": func.__doc__,
            },
        )

        pid = feature_id or f"{func.__module__}.{class_name}"
        return _feature_class(dynamic_class, pid)

    def _do_register(
        obj: type[T] | Callable[[Model], FeatureResult | BaseModel | object],
    ) -> type[BaseFeature[FeatureResult]] | type[T]:
        if isinstance(obj, type):
            return _feature_class(obj)
        return _feature_function(obj)

    if _cls is not None:
        return _do_register(_cls)

    return _do_register
