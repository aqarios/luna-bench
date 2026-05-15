import functools
from collections.abc import Callable
from typing import Any, cast, overload

from dependency_injector.wiring import Provide, inject

from luna_bench._internal.registries.protocols import Registry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench.custom.base_components.base_feature import BaseFeature
from luna_bench.custom.base_components.base_metric import BaseMetric
from luna_bench.custom.base_components.base_plot import BasePlot
from luna_bench.custom.result_containers.benchmark_result_container import BenchmarkResultContainer

from .decorator_utilities import DecoratorUtilities

_REQUIRED_TYPES = BaseFeature[Any] | BaseMetric[Any]


def _resolve_components(
    required_components: type[_REQUIRED_TYPES] | list[type[_REQUIRED_TYPES]] | tuple[type[_REQUIRED_TYPES], ...] | None,
) -> tuple[list[type[BaseFeature[Any]]], list[type[BaseMetric[Any]]]]:
    if required_components is not None:
        return DecoratorUtilities.split_components(required_components)
    return [], []


@overload
def plot(
    required_components: type[BasePlot],
    *,
    plot_id: str | None = None,
    plot_registry: Registry[BasePlot] = Provide[RegistryContainer.plot_registry],
) -> type[BasePlot]: ...


@overload
def plot(
    required_components: Callable[[BenchmarkResultContainer], None],
    *,
    plot_id: str | None = None,
    plot_registry: Registry[BasePlot] = Provide[RegistryContainer.plot_registry],
) -> type[BasePlot]: ...


@overload
def plot(
    required_components: type[_REQUIRED_TYPES],
    *,
    plot_id: str | None = None,
    plot_registry: Registry[BasePlot] = Provide[RegistryContainer.plot_registry],
) -> Callable[[type[BasePlot] | Callable[[BenchmarkResultContainer], None]], type[BasePlot]]: ...


@overload
def plot(
    required_components: list[type[_REQUIRED_TYPES]] | tuple[type[_REQUIRED_TYPES], ...],
    *,
    plot_id: str | None = None,
    plot_registry: Registry[BasePlot] = Provide[RegistryContainer.plot_registry],
) -> Callable[[type[BasePlot] | Callable[[BenchmarkResultContainer], None]], type[BasePlot]]: ...


@overload
def plot(
    required_components: None = None,
    *,
    plot_id: str | None = None,
    plot_registry: Registry[BasePlot] = Provide[RegistryContainer.plot_registry],
) -> Callable[[type[BasePlot] | Callable[[BenchmarkResultContainer], None]], type[BasePlot]]: ...


@inject
def plot(
    required_components: type[BasePlot]
    | Callable[[BenchmarkResultContainer], None]
    | list[type[_REQUIRED_TYPES]]
    | tuple[type[_REQUIRED_TYPES], ...]
    | type[_REQUIRED_TYPES]
    | None = None,
    *,
    plot_id: str | None = None,
    plot_registry: Registry[BasePlot] = Provide[RegistryContainer.plot_registry],
) -> Callable[[type[BasePlot] | Callable[[BenchmarkResultContainer], None]], type[BasePlot]] | type[BasePlot]:
    """
    Register a class or function as a plot component.

    This decorator registers visualization components that consume benchmark results. You can
    register a class inheriting from ``BasePlot`` or wrap a function that handles the plotting
    logic. Plots can declare dependencies on specific metrics or features they need to function.

    Parameters
    ----------
    required_components: type[BasePlot] | Callable | type[BaseFeature] | type[BaseMetric] | list | tuple | None
        The plot to register or its dependencies. Can be:

        - A class inheriting from ``BasePlot`` (bare ``@plot``)
        - A function taking benchmark_results and returning None
        - A single ``BaseMetric`` or ``BaseFeature`` type (becomes a dependency)
        - A list or tuple of ``BaseMetric`` and/or ``BaseFeature`` types (dependencies)

        When dependencies are passed, the decorator returns a decorator function that
        expects a plot class or function as its argument.

    plot_id: str, optional
        Custom identifier for this plot in the registry. If omitted, an ID is
        auto-generated from the module and class/function name.
    plot_registry: Registry[BasePlot]
        The registry where this plot will be stored. Injected by the container. You do not need to set it.

    Returns
    -------
    type[BasePlot] | Callable
        The registered plot class, or a decorator if dependencies were specified.

    Notes
    -----
    When decorating a function, it will be wrapped in a ``BasePlot`` subclass automatically.
    The function receives the full ``BenchmarkResults`` object and is responsible for
    extracting the data it needs to render the plot.

    Examples
    --------
    Basic plot from a class:

    >>> from luna_bench.base_components import BasePlot
    >>> from luna_bench.base_components.data_types.benchmark_results import BenchmarkResults
    >>>
    >>> @plot
    ... class MyPlot(BasePlot):
    ...     def run(self, benchmark_results: BenchmarkResults) -> None:
    ...         # Plot or visualization the data

    Basic plot from a function:

    >>> @plot
    ... def quick_plot(benchmark_results: BenchmarkResultContainer) -> None:
    ...      # Plot or visualization the data

    Plot that depends on a specific metric:

    >>> from luna_bench.components.metrics.runtime import Runtime
    >>>
    >>> @plot(Runtime)
    ... class RuntimeVisualization(BasePlot):
    ...     def run(self, benchmark_results: BenchmarkResultContainer) -> None:
    ...         # Plot or visualization the data

    Plot that depends on multiple metrics:

    >>> @plot([Runtime, Feasibility])
    ... class ComparisonPlot(BasePlot):
    ...     def run(self, benchmark_results: BenchmarkResultContainer) -> None:
    ...         # Render side-by-side comparison

    """
    # Determine whether the first argument is the decorator target or a component list/single component
    is_component = isinstance(required_components, (list, tuple)) or (
        isinstance(required_components, type) and issubclass(required_components, (BaseFeature, BaseMetric))
    )

    target: type[BasePlot] | Callable[[BenchmarkResultContainer], None] | None = (
        None
        if is_component
        else cast("type[BasePlot] | Callable[[BenchmarkResultContainer], None] | None", required_components)
    )
    components: type[_REQUIRED_TYPES] | list[type[_REQUIRED_TYPES]] | tuple[type[_REQUIRED_TYPES], ...] | None = (
        cast(
            "type[_REQUIRED_TYPES] | list[type[_REQUIRED_TYPES]] | tuple[type[_REQUIRED_TYPES], ...] | None",
            required_components,
        )
        if is_component
        else None
    )

    resolved_features, resolved_metrics = _resolve_components(components)

    def _do_register_class(cls: type[BasePlot]) -> type[BasePlot]:
        pid = plot_id or f"{cls.__module__}.{cls.__qualname__}"

        cls.required_features = resolved_features
        cls.required_metrics = resolved_metrics

        DecoratorUtilities.register_class(cls, base=BasePlot, registered_class_id=pid, registry=plot_registry)

        return cls

    def _plot_function(func: Callable[[BenchmarkResultContainer], None]) -> type[BasePlot]:
        class_name = func.__name__

        @functools.wraps(func)
        def run(self: BasePlot, benchmark_results: BenchmarkResultContainer) -> None:
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

    def _do_register(obj: type[BasePlot] | Callable[[BenchmarkResultContainer], None]) -> type[BasePlot]:
        if isinstance(obj, type):
            return _do_register_class(obj)
        return _plot_function(obj)

    if target is not None:
        return _do_register(target)

    return _do_register
