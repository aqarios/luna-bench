from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import containers, providers
from pydantic import BaseModel

from luna_bench._internal.interfaces import IFeature, IMetric, IPlot
from luna_bench._internal.interfaces.algorithm_async import AlgorithmAsync
from luna_bench._internal.interfaces.algorithm_sync import AlgorithmSync

from .arbitrary_data_registry import ArbitraryDataRegistry

if TYPE_CHECKING:
    from dependency_injector.providers import Provider

    from luna_bench._internal.domain_models import RegisteredDataDomain

    from .protocols import PydanticRegistry


class RegistryContainer(containers.DeclarativeContainer):
    feature_registry: Provider[PydanticRegistry[IFeature, RegisteredDataDomain]] = providers.ThreadSafeSingleton(
        ArbitraryDataRegistry[IFeature], kind="feature"
    )

    algorithm_sync_registry: Provider[PydanticRegistry[AlgorithmSync, RegisteredDataDomain]] = (
        providers.ThreadSafeSingleton(ArbitraryDataRegistry[AlgorithmSync], kind="algorithm_sync")
    )

    algorithm_async_registry: Provider[PydanticRegistry[AlgorithmAsync[BaseModel], RegisteredDataDomain]] = (
        providers.ThreadSafeSingleton(ArbitraryDataRegistry[AlgorithmAsync[BaseModel]], kind="algorithm_async")
    )

    metric_registry: Provider[PydanticRegistry[IMetric, RegisteredDataDomain]] = providers.ThreadSafeSingleton(
        ArbitraryDataRegistry[IMetric], kind="metric"
    )

    plot_registry: Provider[PydanticRegistry[IPlot, RegisteredDataDomain]] = providers.ThreadSafeSingleton(
        ArbitraryDataRegistry[IPlot], kind="plot"
    )
