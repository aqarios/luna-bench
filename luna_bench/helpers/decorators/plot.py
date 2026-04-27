import functools
from collections.abc import Callable

from dependency_injector.wiring import Provide, inject

from luna_bench._internal.registries.protocols import Registry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench.base_components import BaseFeature, BaseMetric, BasePlot
from luna_bench.base_components.data_types.benchmark_results import BenchmarkResults

from .decorator_utilities import DecoratorUtilities


@inject
def plot(
    _cls: type[BasePlot] | None = None,
    *,
    plot_id: str | None = None,
    required_features: type[BaseFeature] | list[type[BaseFeature]] | tuple[type[BaseFeature], ...] | None = None,
    required_metrics: type[BaseMetric] | list[type[BaseMetric]] | tuple[type[BaseMetric], ...] | None = None,
    plot_registry: Registry[BasePlot] = Provide[RegistryContainer.plot_registry],
) -> Callable[[type[BasePlot]], type[BasePlot]] | type[BasePlot]:
    """
    Register a class or function as a plot.

    The decorated class must be a subclass of the ``BasePlot`` protocol. When decorating a function,
    it must take a data parameter and return None.

    Parameters
    ----------
    _cls : type[BasePlot[Any]] | Callable, optional
        The class or function to be decorated. If None, returns a decorator function.
    metrics_ids : tuple[str] | None, optional
        Tuple of metric IDs that this plot depends on. Default is None.
    features_ids : tuple[str] | None, optional
        Tuple of feature IDs that this plot depends on. Default is None.
    plot_id : str | None, optional
        Set a custom ID for the plot. If not provided, the ID will be generated automatically
        from the module and class/function name. It's recommended to not set this parameter.
    plot_registry : Registry[BasePlot[Any]], injected
        The registry where the plot will be registered. Injected by a dependency container.

    Returns
    -------
    Callable[[type[BasePlot[Any]]], type[BasePlot[Any]]] | type[BasePlot[Any]]
        Either the decorated class/function or a decorator function.
    """

    def _do_register_class(cls: type[BasePlot]) -> type[BasePlot]:
        pid = plot_id or f"{cls.__module__}.{cls.__qualname__}"

        cls.required_features = DecoratorUtilities.convert_to_list(required_features)
        cls.required_metrics = DecoratorUtilities.convert_to_list(required_metrics)

        DecoratorUtilities.register_class(cls, base=BasePlot, registered_class_id=pid, registry=plot_registry)

        return cls

    def _plot_function(func: Callable[[BenchmarkResults], None]) -> type[BasePlot]:
        class_name = func.__name__

        @functools.wraps(func)
        def run(self: BasePlot, benchmark_results: BenchmarkResults) -> None:
            _ = self
            return func(benchmark_results)

        # Create the dynamic class
        dynamic_class: type[BasePlot] = type(
            class_name,
            (BasePlot,),
            {
                "run": run,
                "__module__": func.__module__,
                "__doc__": func.__doc__,
            },
        )

        return _do_register_class(dynamic_class)

    def _do_register(obj: type[BasePlot] | Callable[[BenchmarkResults], None]) -> type[BasePlot]:
        if isinstance(obj, type):
            return _do_register_class(obj)
        return _plot_function(obj)

    if _cls is not None:
        return _do_register(_cls)

    return _do_register
