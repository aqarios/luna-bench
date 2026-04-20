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
def metric[T: BaseMetric](
    _cls: type[T],
    *,
    metric_id: str | None = None,
    required_features: type[BaseFeature] | list[type[BaseFeature]] | tuple[type[BaseFeature], ...] | None = None,
    metric_registry: Registry[BaseMetric] = Provide[RegistryContainer.metric_registry],
) -> type[T]: ...


@overload
def metric[T: BaseMetric](
    _cls: None = None,
    *,
    metric_id: str | None = None,
    required_features: type[BaseFeature] | list[type[BaseFeature]] | tuple[type[BaseFeature], ...] | None = None,
    metric_registry: Registry[BaseMetric] = Provide[RegistryContainer.metric_registry],
) -> Callable[[type[T]], type[T]]: ...


@inject
def metric[T: BaseMetric](
    _cls: type[T] | None = None,
    *,
    metric_id: str | None = None,
    required_features: type[BaseFeature] | list[type[BaseFeature]] | tuple[type[BaseFeature], ...] | None = None,
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

    def _metric_class[T: BaseMetric](cls: type[T], pid: str | None = None) -> type[T]:
        if pid is None:
            pid = metric_id or f"{cls.__module__}.{cls.__qualname__}"
        cls.required_features = DecoratorUtilities._convert_to_list(required_features)
        DecoratorUtilities.register_class(cls, base=BaseMetric, registered_class_id=pid, registry=metric_registry)
        return cls

    def _metric_function(func: Callable[[BaseMetric, Solution, FeatureResults], MetricResult]) -> type[BaseMetric]:
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
        def run(self, solution: Solution, feature_results: FeatureResults) -> MetricResult:
            result = func(solution, feature_results)
            if not isinstance(result, MetricResult):
                return MetricResult.model_construct(result=result)  # type: ignore[call-arg]
            return result  # type: ignore[return-value]

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

    def _do_register(obj: Any) -> Any:
        if isinstance(obj, type):
            return _metric_class(obj)
        return _metric_function(obj)

    if _cls is not None:
        return _do_register(_cls)

    return _do_register
