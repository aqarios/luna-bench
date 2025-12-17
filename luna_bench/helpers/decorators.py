from collections.abc import Callable
from typing import Any, overload

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from pydantic import BaseModel

from luna_bench._internal.registries.protocols import Registry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench.base_components import BaseAlgorithmAsync, BaseAlgorithmSync, BaseFeature, BaseMetric, BasePlot
from luna_bench.errors.incompatible_class_error import IncompatibleClassError


def _register_class(
    register_class: type[BaseMetric | BaseFeature | BaseAlgorithmAsync[Any] | BaseAlgorithmSync | BasePlot[Any]],
    *,
    base: type | tuple[type, ...],
    registered_class_id: str | None,
    registry: Registry[Any],
) -> None:
    if not isinstance(register_class, type) or not issubclass(register_class, base):
        raise IncompatibleClassError(base)
    pid = registered_class_id or f"{register_class.__module__}.{register_class.__qualname__}"
    register_class._registered_id = pid  # noqa: SLF001 # We define it here internally.
    register_class.registered_id = pid  # We define it here internally.

    registry.register(pid, register_class)


def _convert_to_list[T](value: T | list[T] | tuple[T, ...] | None) -> list[T]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


@inject
def feature[T: BaseFeature](
    _cls: type[T] | None = None,
    *,
    feature_id: str | None = None,
    feature_registry: Registry[BaseFeature] = Provide[RegistryContainer.feature_registry],
) -> Callable[[type[T]], type[T]] | type[T]:
    """
    Register a class as a feature.

    Parameters
    ----------
    _cls: type[T], optional
    feature_id: str | None, optional
        Set a custom ID for the feature. If not provided, the ID will be generated automatically.
        It's recommended to not set this parameter.
    feature_registry: Registry[IFeature], injected

    Returns
    -------
    Callable[[type[T]], type[T]] | type[T]

    """

    def _do_register(cls: type[T]) -> type[T]:
        pid = feature_id or f"{cls.__module__}.{cls.__qualname__}"
        _register_class(cls, base=BaseFeature, registered_class_id=pid, registry=feature_registry)
        return cls

    if _cls is not None:
        return _do_register(_cls)

    return _do_register


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
    Register a class as an algorithm.

    The class which should be registered must be a subclass of the ``IAlgorithm`` protocol.

    Parameters
    ----------
    _cls: type[T], optional
    algorithm_id: str | None, optional
        Set a custom ID for the algorithm. If not provided, the ID will be generated automatically.
        It's recommended to not set this parameter.
    algorithm_registry: Registry[IAlgorithm[IBackend]], injected

    Returns
    -------
    Callable[[type[T]], type[T]] | type[T]

    """

    def _do_register(cls: type[T]) -> type[T]:
        pid = algorithm_id or f"{cls.__module__}.{cls.__qualname__}"
        if issubclass(cls, BaseAlgorithmAsync):
            _register_class(cls, base=BaseAlgorithmAsync, registered_class_id=pid, registry=algorithm_async_registry)
        elif issubclass(cls, BaseAlgorithmSync):
            _register_class(cls, base=BaseAlgorithmSync, registered_class_id=pid, registry=algorithm_sync_registry)
        else:
            raise IncompatibleClassError(BaseAlgorithmAsync | BaseAlgorithmSync)
        return cls

    if _cls is not None:
        return _do_register(_cls)

    return _do_register


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

    The class which should be registered must be a subclass of the ``IMetric`` protocol.

    Parameters
    ----------
    _cls: type[T], optional
    metric_id: str | None, optional
        Set a custom ID for the metric. If not provided, the ID will be generated automatically.
        It's recommended to not set this parameter.
    required_features : tuple[IFeature, ...] | None = None
        A tuple of required features for this metric. If none, no features are required.
    metric_registry: Registry[IMetric], injected

    Returns
    -------
    Callable[[type[T]], type[T]] | type[T]

    """
    if required_features is None:
        required_features = []

    def _do_register(cls: type[T]) -> type[T]:
        pid = metric_id or f"{cls.__module__}.{cls.__qualname__}"

        cls.required_features = _convert_to_list(required_features)
        _register_class(cls, base=BaseMetric, registered_class_id=pid, registry=metric_registry)

        return cls

    if _cls is not None:
        return _do_register(_cls)

    return _do_register


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

    The class which should be registered must be a subclass of the ``IPlot`` protocol.

    Parameters
    ----------
    _cls: type[T], optional
    plot_id: str | None, optional
        Set a custom ID for the plot. If not provided, the ID will be generated automatically.
        It's recommended to not set this parameter.
    plot_registry: Registry[IPlot], injected

    Returns
    -------
    Callable[[type[T]], type[T]] | type[T]
    """

    def _do_register(cls: type[BasePlot[Any]]) -> type[BasePlot[Any]]:
        pid = plot_id or f"{cls.__module__}.{cls.__qualname__}"
        _register_class(cls, base=BasePlot, registered_class_id=pid, registry=plot_registry)
        if metrics_ids is not None:
            cls.metrics_ids = metrics_ids
        if features_ids is not None:
            cls.features_ids = features_ids
        return cls

    if _cls is not None:
        return _do_register(_cls)

    return _do_register


@inject
def features(
    feature_registry: Registry[BaseFeature] = Provide[RegistryContainer.feature_registry],
) -> Registry[BaseFeature]:
    """
    Retrieve the feature registry.

    Parameters
    ----------
    feature_registry: Registry[IFeature], injected

    Returns
    -------
    Registry[Feature]
        Returns the injected feature registry.

    """
    return feature_registry


@inject
def algorithms_sync(
    algorithm_registry: Registry[BaseAlgorithmSync] = Provide[RegistryContainer.algorithm_sync_registry],
) -> Registry[BaseAlgorithmSync]:
    """
    Retrieve the algorithm registry.

    Parameters
    ----------
    algorithm_registry: Registry[IAlgorithm[IBackend]], injected

    Returns
    -------
    Registry[IAlgorithm[IBackend]]
        Returns the injected algorithm registry.

    """
    return algorithm_registry


@inject
def algorithms_async(
    algorithm_registry: Registry[BaseAlgorithmAsync[BaseModel]] = Provide[RegistryContainer.algorithm_async_registry],
) -> Registry[BaseAlgorithmAsync[BaseModel]]:
    """
    Retrieve the algorithm registry.

    Parameters
    ----------
    algorithm_registry: Registry[IAlgorithm[IBackend]], injected

    Returns
    -------
    Registry[IAlgorithm[IBackend]]
        Returns the injected algorithm registry.

    """
    return algorithm_registry


@inject
def metrics(
    metric_registry: Registry[BaseMetric] = Provide[RegistryContainer.metric_registry],
) -> Registry[BaseMetric]:
    """
    Retrieve the metric registry.

    Parameters
    ----------
    metric_registry: Registry[IMetric], injected

    Returns
    -------
    Registry[Metric]
        Returns the injected metric registry.

    """
    return metric_registry


@inject
def plots(
    plot_registry: Registry[BasePlot[Any]] = Provide[RegistryContainer.plot_registry],
) -> Registry[BasePlot[Any]]:
    """
    Retrieve the plot registry.

    Parameters
    ----------
    plot_registry: Registry[IPlot], injected

    Returns
    -------
    Registry[Plot]
        Returns the injected plot registry.

    """
    return plot_registry


@inject
def registry_info(
    feature_registry: Registry[BaseFeature] = Provide[RegistryContainer.feature_registry],
    algorithm_sync_registry: Registry[BaseAlgorithmSync] = Provide[RegistryContainer.algorithm_sync_registry],
    algorithm_async_registry: Registry[BaseAlgorithmAsync[BaseModel]] = Provide[
        RegistryContainer.algorithm_async_registry
    ],
    metric_registry: Registry[BaseMetric] = Provide[RegistryContainer.metric_registry],
    plot_registry: Registry[BasePlot[Any]] = Provide[RegistryContainer.plot_registry],
) -> None:
    """
    Print information about the registered features, algorithms, metrics, and plots.

    Parameters
    ----------
    feature_registry: Registry[IFeature], injected
    algorithm_registry: Registry[IAlgorithm[IBackend]], injected
    metric_registry: Registry[IMetric], injected
    plot_registry: Registry[IPlot[Any]], injected


    """
    logging = Logging.get_logger(__name__)
    logging.info(f"FeatureRegistry: {feature_registry.ids()}")
    logging.info(f"AlgorithmSyncRegistry: {algorithm_sync_registry.ids()}")
    logging.info(f"AlgorithmAsyncRegistry: {algorithm_async_registry.ids()}")
    logging.info(f"MetricRegistry: {metric_registry.ids()}")
    logging.info(f"PlotRegistry: {plot_registry.ids()}")
