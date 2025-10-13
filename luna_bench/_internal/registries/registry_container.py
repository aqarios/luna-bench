from dependency_injector import containers, providers
from dependency_injector.providers import Provider
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend

from luna_bench._internal.domain_models import RegisteredDataDomain
from luna_bench._internal.interfaces import IFeature, IMetric, IPlot

from .arbitrary_data_registry import ArbitraryDataRegistry
from .protocols import PydanticRegistry


class RegistryContainer(containers.DeclarativeContainer):
    feature_registry: Provider[PydanticRegistry[IFeature, RegisteredDataDomain]] = providers.ThreadSafeSingleton(
        ArbitraryDataRegistry[IFeature], kind="feature"
    )

    algorithm_registry: Provider[PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain]] = (
        providers.ThreadSafeSingleton(ArbitraryDataRegistry[IAlgorithm[IBackend]], kind="algorithm")
    )

    metric_registry: Provider[PydanticRegistry[IMetric, RegisteredDataDomain]] = providers.ThreadSafeSingleton(
        ArbitraryDataRegistry[IMetric], kind="metric"
    )

    plot_registry: Provider[PydanticRegistry[IPlot, RegisteredDataDomain]] = providers.ThreadSafeSingleton(
        ArbitraryDataRegistry[IPlot], kind="plot"
    )


registry_container = RegistryContainer()
