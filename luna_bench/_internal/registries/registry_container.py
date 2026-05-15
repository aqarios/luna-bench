from __future__ import annotations

from typing import TYPE_CHECKING, Any

from dependency_injector import containers, providers

from luna_bench.custom.base_components.base_algorithm_async import BaseAlgorithmAsync
from luna_bench.custom.base_components.base_algorithm_sync import BaseAlgorithmSync
from luna_bench.custom.base_components.base_feature import BaseFeature
from luna_bench.custom.base_components.base_metric import BaseMetric
from luna_bench.custom.base_components.base_plot import BasePlot

from .arbitrary_data_registry import ArbitraryDataRegistry

if TYPE_CHECKING:
    from dependency_injector.providers import Provider

    from luna_bench._internal.domain_models import RegisteredDataDomain

    from .protocols import PydanticRegistry


class RegistryContainer(containers.DeclarativeContainer):
    feature_registry: Provider[PydanticRegistry[BaseFeature, RegisteredDataDomain]] = providers.ThreadSafeSingleton(
        ArbitraryDataRegistry[BaseFeature], kind="feature"
    )

    algorithm_sync_registry: Provider[PydanticRegistry[BaseAlgorithmSync, RegisteredDataDomain]] = (
        providers.ThreadSafeSingleton(ArbitraryDataRegistry[BaseAlgorithmSync], kind="algorithm_sync")
    )

    algorithm_async_registry: Provider[PydanticRegistry[BaseAlgorithmAsync[Any], RegisteredDataDomain]] = (
        providers.ThreadSafeSingleton(ArbitraryDataRegistry[BaseAlgorithmAsync[Any]], kind="algorithm_async")
    )

    metric_registry: Provider[PydanticRegistry[BaseMetric, RegisteredDataDomain]] = providers.ThreadSafeSingleton(
        ArbitraryDataRegistry[BaseMetric], kind="metric"
    )

    plot_registry: Provider[PydanticRegistry[BasePlot, RegisteredDataDomain]] = providers.ThreadSafeSingleton(
        ArbitraryDataRegistry[BasePlot], kind="plot"
    )
