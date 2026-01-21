from collections.abc import Callable

from dependency_injector.wiring import Provide, inject

from luna_bench._internal.registries.protocols import Registry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench.base_components import BaseMetric

from .decorator_utilities import DecoratorUtilities


@inject
def metric[T: BaseMetric](
    _cls: type[T] | None = None,
    *,
    metric_id: str | None = None,
    metric_registry: Registry[BaseMetric] = Provide[RegistryContainer.metric_registry],
) -> Callable[[type[T]], type[T]] | type[T]:
    """
    Register a class as a metric.

    The class which should be registered must be a subclass of the ``BaseMetric`` protocol.

    Parameters
    ----------
    _cls: type[T], optional
    metric_id: str | None, optional
        Set a custom ID for the metric. If not provided, the ID will be generated automatically.
        It's recommended to not set this parameter.
    metric_registry: Registry[BaseMetric], injected

    Returns
    -------
    Callable[[type[T]], type[T]] | type[T]

    """

    def _do_register(cls: type[T]) -> type[T]:
        pid = metric_id or f"{cls.__module__}.{cls.__qualname__}"
        DecoratorUtilities.register_class(cls, base=BaseMetric, registered_class_id=pid, registry=metric_registry)
        return cls

    if _cls is not None:
        return _do_register(_cls)

    return _do_register
