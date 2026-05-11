import functools
from collections.abc import Callable
from typing import Any, cast, overload

from dependency_injector.wiring import Provide, inject
from luna_model import Solution

from luna_bench._internal.registries.protocols import Registry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench.base_components import BaseFeature, BaseMetric
from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.types import MetricResult

from .decorator_utilities import DecoratorUtilities


def _resolve_features(
    required_components: type[BaseFeature[Any]]
    | list[type[BaseFeature[Any]]]
    | tuple[type[BaseFeature[Any]], ...]
    | None,
) -> list[type[BaseFeature[Any]]]:
    return DecoratorUtilities.convert_to_list(required_components)


@overload
def metric[T: BaseMetric[Any]](
    _cls: type[T],
    *,
    metric_id: str | None = None,
    metric_registry: Registry[BaseMetric[Any]] = Provide[RegistryContainer.metric_registry],
) -> type[T]: ...


@overload
def metric(
    _cls: Callable[[Solution, FeatureResults], MetricResult | float | int],
    *,
    metric_id: str | None = None,
    metric_registry: Registry[BaseMetric[Any]] = Provide[RegistryContainer.metric_registry],
) -> type[BaseMetric[MetricResult]]: ...


@overload
def metric(
    _cls: type[BaseFeature[Any]],
    *,
    metric_id: str | None = None,
    metric_registry: Registry[BaseMetric[Any]] = Provide[RegistryContainer.metric_registry],
) -> Callable[
    [type[BaseMetric[Any]] | Callable[[Solution, FeatureResults], MetricResult | float | int]],
    type[BaseMetric[Any]] | type[BaseMetric[MetricResult]],
]: ...


@overload
def metric(
    _cls: list[type[BaseFeature[Any]]] | tuple[type[BaseFeature[Any]], ...],
    *,
    metric_id: str | None = None,
    metric_registry: Registry[BaseMetric[Any]] = Provide[RegistryContainer.metric_registry],
) -> Callable[
    [type[BaseMetric[Any]] | Callable[[Solution, FeatureResults], MetricResult | float | int]],
    type[BaseMetric[Any]] | type[BaseMetric[MetricResult]],
]: ...


@overload
def metric[T: BaseMetric[Any]](
    _cls: None = None,
    *,
    metric_id: str | None = None,
    metric_registry: Registry[BaseMetric[Any]] = Provide[RegistryContainer.metric_registry],
) -> Callable[
    [type[T] | Callable[[Solution, FeatureResults], MetricResult | float | int]],
    type[T] | type[BaseMetric[MetricResult]],
]: ...


@inject
def metric[T: BaseMetric[Any]](
    _cls: type[BaseMetric[Any]]
    | Callable[[Solution, FeatureResults], MetricResult | float | int]
    | list[type[BaseFeature[Any]]]
    | tuple[type[BaseFeature[Any]], ...]
    | type[BaseFeature[Any]]
    | None = None,
    *,
    metric_id: str | None = None,
    metric_registry: Registry[BaseMetric] = Provide[RegistryContainer.metric_registry],
) -> (
    Callable[
        [type[T] | Callable[[Solution, FeatureResults], MetricResult | float | int]],
        type[T] | type[BaseMetric[MetricResult]],
    ]
    | type[T]
    | type[BaseMetric[MetricResult]]
):
    """
    Register a class or function as a metric component.

    This decorator handles both class-based metrics (inheriting from ``BaseMetric``) and
    function-based metrics. When you decorate a function, it's automatically wrapped in a
    ``BaseMetric`` subclass. You can also declare feature dependencies that your metric
    needs to compute its result.

    Parameters
    ----------
    _cls: type[T] | Callable | type[BaseFeature] | list | tuple | None, optional
        The metric to register. Can be:

        - A class inheriting from ``BaseMetric`` (bare ``@metric``)
        - A function taking (solution, feature_results) and returning float/int/MetricResult
        - A single ``BaseFeature`` type (becomes a dependency)
        - A list or tuple of ``BaseFeature`` types (dependencies)

        When dependencies are passed, the decorator returns a decorator function that
        expects a metric class or function as its argument. In mose cases you don't need
        to set this field at all.

    metric_id: str, optional
        Custom identifier for this metric in the registry. If omitted, an ID is
        auto-generated from the module and class/function name.
    metric_registry: Registry[BaseMetric]
        The registry where this metric will be stored. Injected by the container. You do not need to set it.

    Returns
    -------
    type[T] | type[BaseMetric[MetricResult]] | Callable
        The registered metric class, or a decorator if dependencies were specified.

    Notes
    -----
    When decorating a function, the return type can be:

    - ``float`` or ``int``: automatically wrapped in a ``MetricResult``
    - ``MetricResult``: returned as-is

    The decorated function's signature is validated to ensure it matches the expected
    (solution, feature_results) parameters.

    Examples
    --------
    Basic metric from a class:

    >>> from luna_bench.base_components import BaseMetric
    >>> from luna_model import Solution
    >>> from luna_bench.base_components.data_types.feature_results import FeatureResults
    >>> from luna_bench.types import MetricResult
    >>>
    >>> @metric
    ... class SolutionQuality(BaseMetric):
    ...     def run(self, solution: Solution, feature_results: FeatureResults) -> MetricResult:
    ...         ...
    ...         return MetricResult(result=26.11)

    Basic metric from a function:

    >>> @metric
    ... def solve_time(solution: Solution, feature_results: FeatureResults) -> float:
    ...     return 26.11


    Metric that depends on a feature:

    >>> from luna_bench.base_components import BaseFeature
    >>>
    >>> @metric(Feature1)
    ... def feature_based_metric(solution: Solution, feature_results: FeatureResults) -> float:
    ...     return 26.11

    Metric depending on multiple features:

    >>> @metric([Feature1, Feature2])
    ... def multi_feature_metric(solution: Solution, feature_results: FeatureResults) -> float:
    ...     return 26.11

    """
    # Determine whether the first argument is the decorator target or feature dependencies
    is_feature = isinstance(_cls, (list, tuple)) or (isinstance(_cls, type) and issubclass(_cls, BaseFeature))

    target: type[BaseMetric[Any]] | Callable[[Solution, FeatureResults], MetricResult | float | int] | None = (
        None
        if is_feature
        else cast(
            "type[BaseMetric[Any]] | Callable[[Solution, FeatureResults], MetricResult | float | int] | None", _cls
        )
    )
    required_components: (
        type[BaseFeature[Any]] | list[type[BaseFeature[Any]]] | tuple[type[BaseFeature[Any]], ...] | None
    ) = (
        cast("type[BaseFeature[Any]] | list[type[BaseFeature[Any]]] | tuple[type[BaseFeature[Any]], ...] | None", _cls)
        if is_feature
        else None
    )

    resolved_features = _resolve_features(required_components)

    def _metric_class[U: BaseMetric[Any]](cls: type[U], pid: str | None = None) -> type[U]:
        if pid is None:
            pid = metric_id or f"{cls.__module__}.{cls.__qualname__}"
        cls.required_features = resolved_features
        DecoratorUtilities.register_class(cls, base=BaseMetric, registered_class_id=pid, registry=metric_registry)
        return cls

    def _metric_function(
        func: Callable[[Solution, FeatureResults], MetricResult | float | int],
    ) -> type[BaseMetric[MetricResult]]:
        # Validate the function signature
        DecoratorUtilities.validate_signature(
            func,
            parameter_map={
                "solution": Solution,
                "feature_results": FeatureResults,
            },
        )

        class_name = func.__name__

        @functools.wraps(func)
        def run(
            self: BaseMetric[MetricResult],
            solution: Solution,
            feature_results: FeatureResults,
        ) -> MetricResult:
            _ = self
            result = func(solution, feature_results)
            if not isinstance(result, MetricResult):
                return MetricResult.model_construct(result=result)  # type: ignore[call-arg]
            return result

        # Create the dynamic class
        dynamic_class = type(
            class_name,
            (BaseMetric,),
            {
                "run": run,
                "__module__": func.__module__,
                "__doc__": func.__doc__,
            },
        )

        pid = metric_id or f"{func.__module__}.{class_name}"
        return _metric_class(dynamic_class, pid=pid)

    def _do_register(
        obj: type[T] | Callable[[Solution, FeatureResults], MetricResult | float | int],
    ) -> type[T] | type[BaseMetric[MetricResult]]:
        if isinstance(obj, type):
            return _metric_class(obj)
        return _metric_function(obj)

    if target is not None:
        return _do_register(cast("type[T] | Callable[[Solution, FeatureResults], MetricResult | float | int]", target))

    return _do_register
