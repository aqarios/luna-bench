from collections.abc import Callable
from typing import Any, overload

from dependency_injector.wiring import Provide, inject

from luna_bench._internal.registries.protocols import Registry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench.base_components import BaseAlgorithmAsync, BaseAlgorithmSync
from luna_bench.errors.incompatible_class_error import IncompatibleClassError

from .decorator_utilities import DecoratorUtilities


@overload
def algorithm[T: BaseAlgorithmAsync[Any] | BaseAlgorithmSync](
    _cls: type[T],
    *,
    algorithm_id: str | None = None,
) -> type[T]: ...


@overload
def algorithm[T: BaseAlgorithmAsync[Any] | BaseAlgorithmSync](
    _cls: None = None,
    *,
    algorithm_id: str | None = None,
) -> Callable[[type[T]], type[T]]: ...


@inject
def algorithm[T: BaseAlgorithmAsync[Any] | BaseAlgorithmSync](
    _cls: type[T] | None = None,
    *,
    algorithm_id: str | None = None,
    algorithm_sync_registry: Registry[BaseAlgorithmSync] = Provide[RegistryContainer.algorithm_sync_registry],
    algorithm_async_registry: Registry[BaseAlgorithmAsync[Any]] = Provide[RegistryContainer.algorithm_async_registry],
) -> Callable[[type[T]], type[T]] | type[T]:
    """
    Register a class as an algorithm.

    The class which should be registered must be a subclass of the ``IAlgorithm`` protocol.

    Parameters
    ----------
    _cls: type[T], optional
    algorithm_id: str | None, optional
        Set a custom ID for the algorithm. If not provided, the ID will be generated automatically.
        It's recommended to not set this parameter.
    algorithm_registry: Registry[IAlgorithm[IBackend]], injected

    Returns
    -------
    Callable[[type[T]], type[T]] | type[T]

    """

    def _do_register(cls: type[T]) -> type[T]:
        pid = algorithm_id or f"{cls.__module__}.{cls.__qualname__}"
        if issubclass(cls, BaseAlgorithmAsync):
            DecoratorUtilities.register_class(
                cls, base=BaseAlgorithmAsync, registered_class_id=pid, registry=algorithm_async_registry
            )
        elif issubclass(cls, BaseAlgorithmSync):
            DecoratorUtilities.register_class(
                cls, base=BaseAlgorithmSync, registered_class_id=pid, registry=algorithm_sync_registry
            )
        else:
            raise IncompatibleClassError(BaseAlgorithmAsync | BaseAlgorithmSync)
        return cls

    if _cls is not None:
        return _do_register(_cls)

    return _do_register
