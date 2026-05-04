import functools
from collections.abc import Callable
from typing import Any, overload

from dependency_injector.wiring import Provide, inject
from luna_model import Solution

from luna_bench._internal.registries.protocols import Registry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench.base_components import BaseFeature, BaseMetric
from luna_bench.base_components.data_types.feature_results import FeatureResults
from luna_bench.types import MetricResult

from .decorator_utilities import DecoratorUtilities


@overload
def metric[T: BaseMetric[Any]](
    _cls: type[T],
    *,
    metric_id: str | None = None,
    required_features: type[BaseFeature[Any]]
    | list[type[BaseFeature[Any]]]
    | tuple[type[BaseFeature[Any]], ...]
    | None = None,
    metric_registry: Registry[BaseMetric[Any]] = Provide[RegistryContainer.metric_registry],
) -> type[T]: ...


@overload
def metric(
    _cls: Callable[[Solution, FeatureResults], MetricResult | float | int],
    *,
    metric_id: str | None = None,
    required_features: type[BaseFeature[Any]]
    | list[type[BaseFeature[Any]]]
    | tuple[type[BaseFeature[Any]], ...]
    | None = None,
    metric_registry: Registry[BaseMetric[Any]] = Provide[RegistryContainer.metric_registry],
) -> type[BaseMetric[MetricResult]]: ...


@overload
def metric[T: BaseMetric[Any]](
    _cls: None = None,
    *,
    metric_id: str | None = None,
    required_features: type[BaseFeature[Any]]
    | list[type[BaseFeature[Any]]]
    | tuple[type[BaseFeature[Any]], ...]
    | None = None,
    metric_registry: Registry[BaseMetric[Any]] = Provide[RegistryContainer.metric_registry],
) -> Callable[
    [type[T] | Callable[[Solution, FeatureResults], MetricResult | float | int]],
    type[T] | type[BaseMetric[MetricResult]],
]: ...


@inject
def metric[T: BaseMetric[Any]](
    _cls: type[T] | Callable[[Solution, FeatureResults], MetricResult | float | int] | None = None,
    *,
    metric_id: str | None = None,
    required_features: type[BaseFeature[Any]]
    | list[type[BaseFeature[Any]]]
    | tuple[type[BaseFeature[Any]], ...]
    | None = None,
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
    Register a class or function as a metric.

    The decorated class must be a subclass of the ``BaseMetric`` protocol, or a decorated
    function will be automatically wrapped as a ``BaseMetric`` subclass.

    Parameters
    ----------
    _cls : type[T], optional
        The class to be decorated. If None, returns a decorator function.
    metric_id : str | None, optional
        Set a custom ID for the metric. If not provided, the ID will be generated automatically
        from the module and class/function name. It's recommended to not set this parameter.
    required_features : type[BaseFeature] | list[type[BaseFeature]] | tuple[type[BaseFeature], ...] | None, optional
        Features that this metric depends on. Can be a single feature class or a list/tuple of
        feature classes. Default is None.
    metric_registry : Registry[BaseMetric], injected
        The registry where the metric will be registered. Injected by dependency container.

    Returns
    -------
    Callable[[type[T]], type[T]] | type[T]
        Either the decorated class/function or a decorator function.

    Examples
    --------
    Decorate a class as a metric:

    >>> from luna_bench.base_components import BaseMetric, BaseFeature
    >>> from luna_model import Solution
    >>> from luna_bench.base_components.data_types.feature_results import FeatureResults
    >>> from luna_bench.types import MetricResult
    >>>
    >>> @metric
    ... class MyMetric(BaseMetric):
    ...     def run(self, solution: Solution, feature_results: FeatureResults) -> MetricResult:
    ...         # Calculate and return metric result
    ...         return MetricResult(result=0.95)

    Decorate a function as a metric:

    >>> @metric
    ... def accuracy_metric(solution: Solution, feature_results: FeatureResults) -> float:
    ...     # Calculate accuracy
    ...     return 0.95

    Make a metric dependent on a feature:

    >>>
    >>> @metric(required_features=MyFeature)
    ... def feature_dependent_metric(solution: Solution, feature_results: FeatureResults) -> float:
    ...     my_feature_data = feature_results["MyFeature"]
    ...     return 0.92

    """

    def _metric_class[U: BaseMetric[Any]](cls: type[U], pid: str | None = None) -> type[U]:
        if pid is None:
            pid = metric_id or f"{cls.__module__}.{cls.__qualname__}"
        cls.required_features = DecoratorUtilities.convert_to_list(required_features)
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

    if _cls is not None:
        return _do_register(_cls)

    return _do_register
