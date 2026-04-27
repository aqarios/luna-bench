import functools
from collections.abc import Callable
from typing import Any, overload

from dependency_injector.wiring import Provide, inject
from luna_model import Model, Solution

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
    Register a class or function as an algorithm.

    The decorated class must be a subclass of the ``BaseAlgorithmSync`` or ``BaseAlgorithmAsync`` protocol.
    When decorating a function, it must be a synchronous algorithm that takes a ``Model`` and returns a ``Solution``.

    Parameters
    ----------
    _cls : type[T] | Callable[[Model], Solution], optional
        The class or function to be decorated. If None, returns a decorator function.
    algorithm_id : str | None, optional
        Set a custom ID for the algorithm. If not provided, the ID will be generated automatically
        from the module and class/function name. It's recommended to not set this parameter.
    algorithm_sync_registry : Registry[BaseAlgorithmSync], injected
        The registry where synchronous algorithms will be registered. Injected by dependency container.
    algorithm_async_registry : Registry[BaseAlgorithmAsync[Any]], injected
        The registry where asynchronous algorithms will be registered. Injected by dependency container.

    Returns
    -------
    Callable[[type[T]], type[T]] | type[T]
        Either the decorated class/function or a decorator function.

    Examples
    --------
    Decorate a class as a synchronous algorithm:

    >>> from luna_bench.base_components import BaseAlgorithmSync
    >>> from luna_model import Model, Solution
    >>>
    >>> @algorithm
    ... class MyAlgorithm(BaseAlgorithmSync):
    ...     def run(self, model: Model) -> Solution:
    ...         # Run algorithm and return solution
    ...         return Solution(...)

    Decorate a function as a synchronous algorithm:

    >>> @algorithm
    ... def simple_algorithm(model: Model) -> Solution:
    ...     # Run algorithm and return solution
    ...     return Solution(...)

    Decorate a class as an asynchronous algorithm:

    >>> from luna_bench.base_components import BaseAlgorithmAsync
    >>> from pydantic import BaseModel
    >>> from returns.result import Result
    >>>
    >>> class QuantumState(BaseModel):
    ...     job_id: str
    >>> @algorithm
    ... class QuantumAlgorithm(BaseAlgorithmAsync[QuantumState]):
    ...     @property
    ...     def model_type(self) -> type[QuantumState]:
    ...         return QuantumState
    ...
    ...     def run_async(self, model: Model) -> QuantumState:
    ...         # Submit job and return retrieval data
    ...         return QuantumState(job_id="123")
    ...
    ...     def fetch_result(self, model: Model, retrieval_data: QuantumState) -> Result[Solution, str]:
    ...         # Fetch result using retrieval data
    ...         return Ok(Solution(...))

    Use a custom algorithm ID:

    >>> @algorithm(algorithm_id="custom.my_algorithm")
    ... def my_algorithm(model: Model) -> Solution:
    ...     return Solution(...)

    """

    def _do_register_class(cls: type[T]) -> type[T]:
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

    def _algorithm_function(func: Callable[[Model], Solution]) -> type[BaseAlgorithmSync]:
        # Validate the function signature
        DecoratorUtilities.validate_signature(
            func,
            parameter_map={
                "model": Model,
            },
        )

        class_name = func.__name__

        @functools.wraps(func)
        def run(self: BaseAlgorithmSync, model: Model) -> Solution:
            _ = self
            result = func(model)
            if not isinstance(result, Solution):
                raise TypeError(f"Algorithm function must return a Solution, got {type(result)}")
            return result

        # Create the dynamic class
        dynamic_class = type(
            class_name,
            (BaseAlgorithmSync,),
            {
                "run": run,
                "__module__": func.__module__,
                "__doc__": func.__doc__,
            },
        )

        return _do_register_class(dynamic_class)

    def _do_register(obj: T | type[T]) -> T:
        if isinstance(obj, type):
            return _do_register_class(obj)
        return _algorithm_function(obj)

    if _cls is not None:
        return _do_register(_cls)

    return _do_register
