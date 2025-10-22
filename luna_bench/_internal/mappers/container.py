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
    from luna_bench._internal.user_models.algorithm_usermodel import AlgorithmUserModel
    from luna_bench._internal.user_models.benchmark_usermodel import BenchmarkUserModel
    from luna_bench._internal.user_models.feature_usermodel import FeatureUserModel
    from luna_bench._internal.user_models.metric_usermodel import MetricUserModel
    from luna_bench._internal.user_models.plot_usermodel import PlotUserModel

    from .types import Mapper


class MapperContainer(containers.DeclarativeContainer):
    registry_container = providers.Container(RegistryContainer)

    algorithm_mapper: Provider[Mapper[AlgorithmDomain, AlgorithmUserModel]] = providers.Factory(
        AlgorithmMapper,
        algorithm_registry=registry_container.algorithm_registry,
    )

    feature_mapper: Provider[Mapper[FeatureDomain, FeatureUserModel]] = providers.Factory(
        FeatureMapper,
        feature_registry=registry_container.feature_registry,
    )

    metric_mapper: Provider[Mapper[MetricDomain, MetricUserModel]] = providers.Factory(
        MetricMapper,
        metric_registry=registry_container.metric_registry,
    )

    plot_mapper: Provider[Mapper[PlotDomain, PlotUserModel]] = providers.Factory(
        PlotMapper,
        plot_registry=registry_container.plot_registry,
    )

    benchmark_mapper: Provider[Mapper[BenchmarkDomain, BenchmarkUserModel]] = providers.Factory(
        BenchmarkMapper,
        feature_mapper=feature_mapper,
        metric_mapper=metric_mapper,
        algorithm_mapper=algorithm_mapper,
        plot_mapper=plot_mapper,
    )


mapper_container = MapperContainer()

# Import and override the registry_container to use the global singleton
from luna_bench._internal.registries.registry_container import registry_container  # noqa: E402

mapper_container.registry_container.override(registry_container)
