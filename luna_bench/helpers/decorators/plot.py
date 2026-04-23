import functools
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from dependency_injector.wiring import Provide, inject

from luna_bench._internal.registries.protocols import Registry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench.base_components import BaseFeature, BaseMetric, BasePlot

from .decorator_utilities import DecoratorUtilities

if TYPE_CHECKING:
    from luna_bench.entities.benchmark_entity import BenchmarkEntity


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
        The registry where the plot will be registered. Injected by dependency container.

    Returns
    -------
    Callable[[type[BasePlot[Any]]], type[BasePlot[Any]]] | type[BasePlot[Any]]
        Either the decorated class/function or a decorator function.

    Examples
    --------
    Decorate a class as a plot:

    >>> from luna_bench.base_components import BasePlot
    >>> from luna_bench.entities.benchmark_entity import BenchmarkEntity
    >>> from returns.result import Result
    >>>
    >>> @plot(metrics_ids=("accuracy", "precision"))
    ... class MyPlot(BasePlot[dict]):
    ...     def run(self, data: dict) -> None:
    ...         # Generate and save plot using data
    ...         pass
    ...
    ...     def validate_plot(self, benchmark: BenchmarkEntity) -> Result[dict, Exception]:
    ...         # Validate plot data from benchmark
    ...         return Ok(benchmark_data)

    Decorate a function as a plot:

    >>> import matplotlib.pyplot as plt
    >>>
    >>> @plot(metrics_ids=("accuracy",))
    ... def simple_plot(data: dict) -> None:
    ...     plt.figure()
    ...     plt.plot(data["values"])
    ...     plt.savefig("plot.png")

    Use custom metric and feature IDs:

    >>> @plot(metrics_ids=("accuracy", "precision"), features_ids=("image_size",), plot_id="custom.comparison_plot")
    ... def comparison_plot(data: dict) -> None:
    ...     # Create comparison plot
    ...     pass

    """

    def _do_register_class(cls: type[BasePlot]) -> type[BasePlot]:
        pid = plot_id or f"{cls.__module__}.{cls.__qualname__}"

        cls.required_features = DecoratorUtilities._convert_to_list(required_features)
        cls.required_metrics = DecoratorUtilities._convert_to_list(required_metrics)

        DecoratorUtilities.register_class(cls, base=BasePlot, registered_class_id=pid, registry=plot_registry)

        return cls

    def _plot_function(func: Callable[[Any], None]) -> type[BasePlot]:
        class_name = func.__name__

        @functools.wraps(func)
        def run(self: BasePlot, data: Any) -> None:
            return func(data)

        @functools.wraps(func)
        def validate_plot(self: BasePlot, benchmark: "BenchmarkEntity") -> "Result[Any, Exception]":
            # For function-based plots, return the benchmark data as-is
            from returns.result import Success

            return Success(benchmark)

        # Create the dynamic class
        dynamic_class = type(
            class_name,
            (BasePlot,),
            {
                "run": run,
                "validate_plot": validate_plot,
                "__module__": func.__module__,
                "__doc__": func.__doc__,
            },
        )

        return _do_register_class(dynamic_class)

    def _do_register(obj: Any) -> Any:
        if isinstance(obj, type):
            return _do_register_class(obj)
        return _plot_function(obj)

    if _cls is not None:
        return _do_register(_cls)

    return _do_register
