from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from returns.result import Result, Success

from luna_bench._internal.domain_models import BenchmarkDomain, BenchmarkStatus
from luna_bench._internal.domain_models.algorithm_domain import AlgorithmDomain
from luna_bench._internal.domain_models.algorithm_type_enum import AlgorithmType
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.feature_domain import FeatureDomain
from luna_bench._internal.domain_models.metric_domain import MetricDomain
from luna_bench._internal.domain_models.model_metadata_domain import ModelMetadataDomain
from luna_bench._internal.domain_models.modelset_domain import ModelSetDomain
from luna_bench._internal.domain_models.registered_data_domain import RegisteredDataDomain
from luna_bench._internal.mappers.algorithm_mapper import AlgorithmMapper
from luna_bench._internal.mappers.benchmark_mapper import BenchmarkMapper
from luna_bench._internal.mappers.feature_mapper import FeatureMapper
from luna_bench._internal.mappers.metric_mapper import MetricMapper
from luna_bench._internal.mappers.plot_mapper import PlotMapper
from luna_bench._internal.registries.arbitrary_data_registry import ArbitraryDataRegistry
from luna_bench.base_components import BaseAlgorithmAsync, BaseAlgorithmSync, BaseFeature, BaseMetric, BasePlot
from luna_bench.entities import (
    AlgorithmEntity,
    BenchmarkEntity,
    FeatureEntity,
    MetricEntity,
    ModelMetadataEntity,
    ModelSetEntity,
    PlotEntity,
)
from luna_bench.entities.enums import JobStatus
from tests.unit.fixtures.mock_components import MockAlgorithm, MockAsyncAlgorithm, MockFeature, MockMetric, MockPlot
from tests.utils.luna_model import simple_model

if TYPE_CHECKING:
    from pydantic import ValidationError

    from luna_bench.errors.registry.unknown_id_error import UnknownIdError


def _empty_benchmark_usermodel(name: str) -> BenchmarkEntity:
    return BenchmarkEntity(
        name=name,
        modelset=None,
        features=[],
        algorithms=[],
        metrics=[],
        plots=[],
    )


def _full_benchmark_usermodel(name: str) -> BenchmarkEntity:
    from tests.unit.fixtures.mock_components import MockFeature

    return BenchmarkEntity(
        name=name,
        modelset=ModelSetEntity(
            name="existing",
            id=1,
            models=[
                ModelMetadataEntity(
                    id=1,
                    name="existing",
                    hash=simple_model("existing").__hash__(),
                )
            ],
        ),
        features=[FeatureEntity(name="existing", status=JobStatus.CREATED, feature=MockFeature(), results={})],
        algorithms=[
            AlgorithmEntity(name="existing", status=JobStatus.CREATED, algorithm=MockAlgorithm(), results={}),
            AlgorithmEntity(
                name="existing_async", status=JobStatus.CREATED, algorithm=MockAsyncAlgorithm(), results={}
            ),
        ],
        metrics=[MetricEntity(name="existing", status=JobStatus.CREATED, metric=MockMetric(), results={})],
        plots=[PlotEntity(name="existing", status=JobStatus.CREATED, plot=MockPlot())],
    )


def _empty_domainmodel(name: str) -> BenchmarkDomain:
    return BenchmarkDomain(
        name=name,
        modelset=None,
        features=[],
        algorithms=[],
        metrics=[],
        plots=[],
        status=BenchmarkStatus.CREATED,
    )


def _full_domainmodel(name: str) -> BenchmarkDomain:
    from luna_bench._internal.domain_models import PlotDomain

    return BenchmarkDomain(
        name=name,
        modelset=ModelSetDomain(
            id=1,
            name="existing",
            models=[
                ModelMetadataDomain(
                    id=1,
                    name="existing",
                    hash=simple_model("existing").__hash__(),
                )
            ],
        ),
        features=[
            FeatureDomain(
                name="existing",
                status=JobStatus.CREATED,
                results={},
                config_data=RegisteredDataDomain(registered_id="feature", data=ArbitraryDataDomain()),
            )
        ],
        algorithms=[
            AlgorithmDomain(
                name="existing",
                status=JobStatus.CREATED,
                algorithm_type=AlgorithmType.SYNC,
                results={},
                config_data=RegisteredDataDomain(registered_id="algorithm", data=ArbitraryDataDomain()),
            ),
            AlgorithmDomain(
                name="existing_async",
                status=JobStatus.CREATED,
                algorithm_type=AlgorithmType.ASYNC,
                results={},
                config_data=RegisteredDataDomain(registered_id="algorithm_async", data=ArbitraryDataDomain()),
            ),
        ],
        metrics=[
            MetricDomain(
                name="existing",
                status=JobStatus.CREATED,
                results={},
                config_data=RegisteredDataDomain(registered_id="metric", data=ArbitraryDataDomain()),
            )
        ],
        plots=[
            PlotDomain(
                name="existing",
                status=JobStatus.CREATED,
                config_data=RegisteredDataDomain(registered_id="plot", data=ArbitraryDataDomain()),
            )
        ],
        status=BenchmarkStatus.CREATED,
    )


class TestUtils:
    @pytest.fixture()
    def mappers(
        self,
    ) -> tuple[
        FeatureMapper,
        MetricMapper,
        AlgorithmMapper,
        PlotMapper,
    ]:
        metric_registry = ArbitraryDataRegistry[BaseMetric]("metric")
        feature_registry = ArbitraryDataRegistry[BaseFeature]("feature")
        algorithm_sync_registry = ArbitraryDataRegistry[BaseAlgorithmSync]("algorithm_sync")
        algorithm_async_registry = ArbitraryDataRegistry[BaseAlgorithmAsync[Any]]("algorithm_async")
        plot_registry = ArbitraryDataRegistry[BasePlot]("plot")

        feature_registry.register("feature", MockFeature)
        metric_registry.register("metric", MockMetric)
        algorithm_sync_registry.register("algorithm", MockAlgorithm)
        algorithm_async_registry.register("algorithm_async", MockAsyncAlgorithm)
        plot_registry.register("plot", MockPlot)

        feature_mapper = FeatureMapper(feature_registry)
        metric_mapper = MetricMapper(metric_registry)
        algorithm_mapper = AlgorithmMapper(algorithm_sync_registry, algorithm_async_registry)
        plot_mapper = PlotMapper(plot_registry)

        return feature_mapper, metric_mapper, algorithm_mapper, plot_mapper

    @pytest.mark.parametrize(
        ("benchmark_domain", "exp"),
        [
            (_empty_domainmodel("name"), Success(_empty_benchmark_usermodel("name"))),
            (_full_domainmodel("name"), Success(_full_benchmark_usermodel("name"))),
        ],
    )
    def test_convert_to_user_model(
        self,
        mappers: tuple[
            FeatureMapper,
            MetricMapper,
            AlgorithmMapper,
            PlotMapper,
        ],
        benchmark_domain: BenchmarkDomain,
        exp: Result[BenchmarkEntity, UnknownIdError | ValidationError],
    ) -> None:
        r = BenchmarkMapper(
            mappers[0],
            mappers[1],
            mappers[2],
            mappers[3],
        ).to_user_model(benchmark_domain)
        assert type(r) is type(exp)
        assert r.unwrap() == exp.unwrap()
