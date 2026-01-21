from collections.abc import Callable
from typing import Any

from dependency_injector.wiring import Provide, inject

from luna_bench._internal.registries.protocols import Registry
from luna_bench._internal.registries.registry_container import RegistryContainer

from ...base_components import BasePlot
from .decorator_utilities import DecoratorUtilities


@inject
def plot(
    _cls: type[BasePlot[Any]] | None = None,
    *,
    metrics_ids: tuple[str] | None = None,
    features_ids: tuple[str] | None = None,
    plot_id: str | None = None,
    plot_registry: Registry[BasePlot[Any]] = Provide[RegistryContainer.plot_registry],
) -> Callable[[type[BasePlot[Any]]], type[BasePlot[Any]]] | type[BasePlot[Any]]:
    """
    Register a class as a plot.

    The class which should be registered must be a subclass of the ``BasePlot`` protocol.

    Parameters
    ----------
    _cls: type[T], optional
    plot_id: str | None, optional
        Set a custom ID for the plot. If not provided, the ID will be generated automatically.
        It's recommended to not set this parameter.
    plot_registry: Registry[BasePlot], injected

    Returns
    -------
    Callable[[type[T]], type[T]] | type[T]
    """

    def _do_register(cls: type[BasePlot[Any]]) -> type[BasePlot[Any]]:
        pid = plot_id or f"{cls.__module__}.{cls.__qualname__}"
        DecoratorUtilities.register_class(cls, base=BasePlot, registered_class_id=pid, registry=plot_registry)
        if metrics_ids is not None:
            cls.metrics_ids = metrics_ids  # type: ignore[attr-defined]
        if features_ids is not None:
            cls.features_ids = features_ids  # type: ignore[attr-defined]
        return cls

    if _cls is not None:
        return _do_register(_cls)

    return _do_register
