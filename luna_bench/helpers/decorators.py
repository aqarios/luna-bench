from collections.abc import Callable
from typing import Any

from dependency_injector.wiring import Provide, inject
from luna_quantum import Logging
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend

from luna_bench._internal.interfaces import IFeature, IMetric, IPlot
from luna_bench._internal.registries.protocols import Registry
from luna_bench._internal.registries.registry_container import RegistryContainer
from luna_bench.errors.incompatible_class_error import IncompatibleClassError


def _register_class(
    register_class: type[Any],
    *,
    base: type,
    registered_class_id: str | None,
    registry: Registry[Any],
) -> None:
    if not isinstance(register_class, type) or not issubclass(register_class, base):
        raise IncompatibleClassError(base)
    pid = registered_class_id or f"{register_class.__module__}.{register_class.__qualname__}"

    register_class._registered_id = pid  # type: ignore[attr-defined] # noqa: SLF001 # We define it here internally.
    registry.register(pid, register_class)


@inject
def feature[T: IFeature](
    _cls: type[T] | None = None,
    *,
    feature_id: str | None = None,
    feature_registry: Registry[IFeature] = Provide[RegistryContainer.feature_registry],
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
        _register_class(cls, base=IFeature, registered_class_id=pid, registry=feature_registry)
        return cls

    if _cls is not None:
        return _do_register(_cls)

    return _do_register


@inject
def algorithm[T: IAlgorithm[IBackend]](
    _cls: type[T] | None = None,
    *,
    algorithm_id: str | None = None,
    algorithm_registry: Registry[IAlgorithm[IBackend]] = Provide[RegistryContainer.algorithm_registry],
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
        _register_class(cls, base=IAlgorithm, registered_class_id=pid, registry=algorithm_registry)
        return cls

    if _cls is not None:
        return _do_register(_cls)

    return _do_register


@inject
def metric[T: IMetric](
    _cls: type[T] | None = None,
    *,
    metric_id: str | None = None,
    metric_registry: Registry[IMetric] = Provide[RegistryContainer.metric_registry],
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
    metric_registry: Registry[IMetric], injected

    Returns
    -------
    Callable[[type[T]], type[T]] | type[T]

    """

    def _do_register(cls: type[T]) -> type[T]:
        pid = metric_id or f"{cls.__module__}.{cls.__qualname__}"
        _register_class(cls, base=IMetric, registered_class_id=pid, registry=metric_registry)
        return cls

    if _cls is not None:
        return _do_register(_cls)

    return _do_register


@inject
def plot(
    _cls: type[IPlot] | None = None,
    *,
    metrics: tuple[str] | None = None,
    features: tuple[str] | None = None,
    plot_id: str | None = None,
    plot_registry: Registry[IPlot] = Provide[RegistryContainer.plot_registry],
) -> Callable[[type[IPlot]], type[IPlot]] | type[IPlot]:
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

    def _do_register(cls: type[IPlot]) -> type[IPlot]:
        pid = plot_id or f"{cls.__module__}.{cls.__qualname__}"
        _register_class(cls, base=IPlot, registered_class_id=pid, registry=plot_registry)
        if metrics is not None:
            cls.metrics = metrics  # type: ignore[attr-defined]
        if features is not None:
            cls.features = features  # type: ignore[attr-defined]
        return cls

    if _cls is not None:
        return _do_register(_cls)

    return _do_register


@inject
def features(
    feature_registry: Registry[IFeature] = Provide[RegistryContainer.feature_registry],
) -> Registry[IFeature]:
    """
    Retrieve the feature registry.

    Parameters
    ----------
    feature_registry: Registry[IFeature], injected

    Returns
    -------
    Registry[IFeature]
        Returns the injected feature registry.

    """
    return feature_registry


@inject
def algorithms(
    algorithm_registry: Registry[IAlgorithm[IBackend]] = Provide[RegistryContainer.algorithm_registry],
) -> Registry[IAlgorithm[IBackend]]:
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
    metric_registry: Registry[IMetric] = Provide[RegistryContainer.metric_registry],
) -> Registry[IMetric]:
    """
    Retrieve the metric registry.

    Parameters
    ----------
    metric_registry: Registry[IMetric], injected

    Returns
    -------
    Registry[IMetric]
        Returns the injected metric registry.

    """
    return metric_registry


@inject
def plots(
    plot_registry: Registry[IPlot] = Provide[RegistryContainer.plot_registry],
) -> Registry[IPlot]:
    """
    Retrieve the plot registry.

    Parameters
    ----------
    plot_registry: Registry[IPlot], injected

    Returns
    -------
    Registry[IPlot]
        Returns the injected plot registry.

    """
    return plot_registry


@inject
def registry_info(
    feature_registry: Registry[IFeature] = Provide[RegistryContainer.feature_registry],
    algorithm_registry: Registry[IAlgorithm[IBackend]] = Provide[RegistryContainer.algorithm_registry],
    metric_registry: Registry[IMetric] = Provide[RegistryContainer.metric_registry],
    plot_registry: Registry[IPlot] = Provide[RegistryContainer.plot_registry],
) -> None:
    """
    Print information about the registered features, algorithms, metrics, and plots.

    Parameters
    ----------
    feature_registry: Registry[IFeature], injected
    algorithm_registry: Registry[IAlgorithm[IBackend]], injected
    metric_registry: Registry[IMetric], injected
    plot_registry: Registry[IPlot], injected


    """
    logging = Logging.get_logger(__name__)
    logging.info(f"FeatureRegistry: {feature_registry.ids()}")
    logging.info(f"AlgorithmRegistry: {algorithm_registry.ids()}")
    logging.info(f"MetricRegistry: {metric_registry.ids()}")
    logging.info(f"PlotRegistry: {plot_registry.ids()}")
