import functools
from collections.abc import Callable
from typing import Any, cast, overload

import cloudpickle
from dependency_injector.wiring import Provide, inject
from luna_model import Model, Solution

from luna_bench._internal.registries.protocols import Registry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench.custom.base_components.base_algorithm_async import BaseAlgorithmAsync
from luna_bench.custom.base_components.base_algorithm_sync import BaseAlgorithmSync
from luna_bench.errors.decorators.invalid_return_type_error import InvalidReturnTypeError
from luna_bench.errors.incompatible_class_error import IncompatibleClassError

from .decorator_utilities import DecoratorUtilities


def _rebuild_algorithm(func_bytes: bytes) -> BaseAlgorithmSync:
    """Reconstruct a function-based algorithm from a cloudpickled function.

    Used as the ``__reduce__`` target for dynamic algorithm classes so
    inline ``@algorithm`` decorators can be pickled and deserialized in
    the huey consumer subprocess.
    """
    func = cloudpickle.loads(func_bytes)
    name = func.__name__

    @functools.wraps(func)
    def run(self: BaseAlgorithmSync, model: Model) -> Solution:
        _ = self
        result = func(model)
        if not isinstance(result, Solution):
            raise InvalidReturnTypeError(name, Solution, type(result))
        return result

    cls = type(
        name,
        (BaseAlgorithmSync,),
        {"run": run, "__module__": "luna_bench.custom.decorators.algorithm", "__doc__": func.__doc__},
    )
    return cast("BaseAlgorithmSync", cls())


@overload
def algorithm[T: BaseAlgorithmAsync[Any] | BaseAlgorithmSync](
    _cls: type[T],
    *,
    algorithm_id: str | None = None,
) -> type[T]: ...


@overload
def algorithm(
    _cls: Callable[[Model], Solution],
    *,
    algorithm_id: str | None = None,
) -> type[BaseAlgorithmSync]: ...


@overload
def algorithm[T: BaseAlgorithmAsync[Any] | BaseAlgorithmSync](
    _cls: None = None,
    *,
    algorithm_id: str | None = None,
) -> Callable[[type[T] | Callable[[Model], Solution]], type[T] | type[BaseAlgorithmSync]]: ...


@inject
def algorithm[T: BaseAlgorithmAsync[Any] | BaseAlgorithmSync](
    _cls: type[T] | Callable[[Model], Solution] | None = None,
    *,
    algorithm_id: str | None = None,
    algorithm_sync_registry: Registry[BaseAlgorithmSync] = Provide[RegistryContainer.algorithm_sync_registry],
    algorithm_async_registry: Registry[BaseAlgorithmAsync[Any]] = Provide[RegistryContainer.algorithm_async_registry],
) -> (
    Callable[[type[T] | Callable[[Model], Solution]], type[T] | type[BaseAlgorithmSync]]
    | type[T]
    | type[BaseAlgorithmSync]
):
    """
    Register a class or function as an algorithm.

    The decorated class must be a subclass of ``BaseAlgorithmSync`` or
    ``BaseAlgorithmAsync``.  When decorating a function, it is wrapped in a
    dynamic class and registered with the background task queue.
    """

    def _do_register_class[U: BaseAlgorithmAsync[Any] | BaseAlgorithmSync](cls: type[U]) -> type[U]:
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
            raise IncompatibleClassError((BaseAlgorithmAsync, BaseAlgorithmSync))
        return cls

    def _algorithm_function(func: Callable[[Model], Solution]) -> type[BaseAlgorithmSync]:
        DecoratorUtilities.validate_signature(func, parameter_map={"model": Model})

        @functools.wraps(func)
        def run(self: BaseAlgorithmSync, model: Model) -> Solution:
            _ = self
            result = func(model)
            if not isinstance(result, Solution):
                raise InvalidReturnTypeError(func.__name__, Solution, type(result))
            return result

        dynamic_class = type(
            func.__name__,
            (BaseAlgorithmSync,),
            {
                "run": run,
                "__module__": func.__module__,
                "__doc__": func.__doc__,
                "__reduce__": lambda _: (
                    _rebuild_algorithm,
                    (cloudpickle.dumps(func),),
                ),
            },
        )

        return _do_register_class(dynamic_class)

    def _do_register(
        obj: type[T] | Callable[[Model], Solution],
    ) -> type[T] | type[BaseAlgorithmSync]:
        if isinstance(obj, type):
            return _do_register_class(obj)
        return _algorithm_function(obj)

    if _cls is not None:
        return _do_register(_cls)

    return _do_register
