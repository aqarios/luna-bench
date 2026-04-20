import functools
from collections.abc import Callable
from typing import Any, overload

from dependency_injector.wiring import Provide, inject
from luna_model import Model
from pydantic import BaseModel

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.registries.protocols import Registry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench.base_components import BaseFeature

from .decorator_utilities import DecoratorUtilities


@overload
def feature[T: BaseFeature](
    _cls: type[T],
    *,
    feature_id: str | None = None,
    feature_registry: Registry[BaseFeature] = Provide[RegistryContainer.feature_registry],
) -> type[T]: ...


@overload
def feature[T: BaseFeature](
    _cls: None = None,
    *,
    feature_id: str | None = None,
    feature_registry: Registry[BaseFeature] = Provide[RegistryContainer.feature_registry],
) -> Callable[[type[T]], type[T]]: ...


@inject
def feature[T: BaseFeature](
    _cls: type[T] | None = None,
    *,
    feature_id: str | None = None,
    feature_registry: Registry[BaseFeature] = Provide[RegistryContainer.feature_registry],
) -> Callable[[type[T]], type[T]] | type[T]:
    """
    Register a class or a function as a feature.

    Parameters
    ----------
    _obj: type[Any] | Callable[[BaseFeature, Model], Any], optional
    feature_id: str | None, optional
        Set a custom ID for the feature. If not provided, the ID will be generated automatically.
        It's recommended to not set this parameter.
    feature_registry: Registry[BaseFeature], injected

    Returns
    -------
    Any

    """

    def _feature_class[T: BaseFeature](cls: type[T], pid: str | None = None) -> type[T]:
        if pid is None:
            pid = feature_id or f"{cls.__module__}.{cls.__qualname__}"
        DecoratorUtilities.register_class(cls, base=BaseFeature, registered_class_id=pid, registry=feature_registry)
        return cls

    def _feature_function(func: Callable[[BaseFeature, Model], Any]) -> type[BaseFeature]:
        class_name = func.__name__

        DecoratorUtilities.validate_signature(
            func,
            parameter_map={
                "model": Model,
            },
        )

        @functools.wraps(func)
        def run(self: BaseFeature, model: Model) -> ArbitraryDataDomain:
            result = func(model)
            if not isinstance(result, BaseModel):
                return ArbitraryDataDomain.model_construct(result=result)  # type: ignore[call-arg]
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

    def _do_register(obj: Any) -> Any:
        if isinstance(obj, type):
            return _feature_class(obj)
        return _feature_function(obj)

    if _cls is not None:
        return _do_register(_cls)

    return _do_register
