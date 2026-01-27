from __future__ import annotations

from typing import TYPE_CHECKING

from dependency_injector import containers, providers

from luna_bench._internal.mappers.algorithm_mapper import AlgorithmMapper
from luna_bench._internal.mappers.benchmark_mapper import BenchmarkMapper
from luna_bench._internal.mappers.feature_mapper import FeatureMapper
from luna_bench._internal.mappers.metric_mapper import MetricMapper
from luna_bench._internal.mappers.plot_mapper import PlotMapper
from luna_bench._internal.registries.registry_container import RegistryContainer

if TYPE_CHECKING:
    from dependency_injector.providers import Provider

    from luna_bench._internal.domain_models.algorithm_domain import AlgorithmDomain
    from luna_bench._internal.domain_models.benchmark_domain import BenchmarkDomain
    from luna_bench._internal.domain_models.feature_domain import FeatureDomain
    from luna_bench._internal.domain_models.metric_domain import MetricDomain
    from luna_bench._internal.domain_models.plot_config_domain import PlotDomain
    from luna_bench._internal.mappers.base_mapper import Mapper
    from luna_bench.entities.algorithm_entity import AlgorithmEntity
    from luna_bench.entities.benchmark_entity import BenchmarkEntity
    from luna_bench.entities.feature_entity import FeatureEntity
    from luna_bench.entities.metric_entity import MetricEntity
    from luna_bench.entities.plot_entity import PlotEntity


class MapperContainer(containers.DeclarativeContainer):
    registry_container = providers.Container(RegistryContainer)

    algorithm_mapper: Provider[Mapper[AlgorithmDomain, AlgorithmEntity]] = providers.Factory(
        AlgorithmMapper,
        algorithm_sync_registry=registry_container.algorithm_sync_registry,
        algorithm_async_registry=registry_container.algorithm_async_registry,
    )
    algorithm_async_mapper: Provider[Mapper[AlgorithmDomain, AlgorithmEntity]] = providers.Factory(
        AlgorithmMapper,
        algorithm_registry=registry_container.algorithm_async_registry,
    )

    feature_mapper: Provider[Mapper[FeatureDomain, FeatureEntity]] = providers.Factory(
        FeatureMapper,
        feature_registry=registry_container.feature_registry,
    )

    metric_mapper: Provider[Mapper[MetricDomain, MetricEntity]] = providers.Factory(
        MetricMapper,
        metric_registry=registry_container.metric_registry,
    )

    plot_mapper: Provider[Mapper[PlotDomain, PlotEntity]] = providers.Factory(
        PlotMapper,
        plot_registry=registry_container.plot_registry,
    )

    benchmark_mapper: Provider[Mapper[BenchmarkDomain, BenchmarkEntity]] = providers.Factory(
        BenchmarkMapper,
        feature_mapper=feature_mapper,
        metric_mapper=metric_mapper,
        algorithm_mapper=algorithm_mapper,
        plot_mapper=plot_mapper,
    )
