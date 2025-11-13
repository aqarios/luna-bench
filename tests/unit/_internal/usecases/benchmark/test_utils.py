from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pytest
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend
from returns.result import Result, Success

from luna_bench._internal.domain_models import BenchmarkDomain, BenchmarkStatus
from luna_bench._internal.domain_models.algorithm_domain import AlgorithmDomain
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.feature_domain import FeatureDomain
from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.domain_models.metric_domain import MetricDomain
from luna_bench._internal.domain_models.registered_data_domain import RegisteredDataDomain
from luna_bench._internal.interfaces import IFeature, IMetric, IPlot
from luna_bench._internal.mappers.algorithm_mapper import AlgorithmMapper
from luna_bench._internal.mappers.benchmark_mapper import BenchmarkMapper
from luna_bench._internal.mappers.feature_mapper import FeatureMapper
from luna_bench._internal.mappers.metric_mapper import MetricMapper
from luna_bench._internal.mappers.plot_mapper import PlotMapper
from luna_bench._internal.registries.arbitrary_data_registry import ArbitraryDataRegistry
from luna_bench._internal.user_models import AlgorithmUserModel, BenchmarkUserModel, MetricUserModel, PlotUserModel
from luna_bench._internal.user_models.feature_usermodel import FeatureUserModel
from tests.unit.fixtures.mock_components import MockAlgorithm, MockFeature, MockMetric, MockPlot

if TYPE_CHECKING:
    from pydantic import ValidationError

    from luna_bench.errors.registry.unknown_id_error import UnknownIdError


def _empty_benchmark_usermodel(name: str) -> BenchmarkUserModel:
    return BenchmarkUserModel(
        name=name,
        modelset=None,
        features=[],
        algorithms=[],
        metrics=[],
        plots=[],
    )


def _full_benchmark_usermodel(name: str) -> BenchmarkUserModel:
    from tests.unit.fixtures.mock_components import MockFeature

    return BenchmarkUserModel(
        name=name,
        modelset=None,
        features=[FeatureUserModel(name="feature", status=JobStatus.CREATED, feature=MockFeature(), results={})],
        algorithms=[AlgorithmUserModel(name="algorithm", status=JobStatus.CREATED, algorithm=MockAlgorithm())],
        metrics=[MetricUserModel(name="metric", status=JobStatus.CREATED, metric=MockMetric())],
        plots=[PlotUserModel(name="plot", status=JobStatus.CREATED, plot=MockPlot())],
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
        modelset=None,
        features=[
            FeatureDomain(
                name="feature",
                status=JobStatus.CREATED,
                results={},
                config_data=RegisteredDataDomain(registered_id="feature", data=ArbitraryDataDomain()),
            )
        ],
        algorithms=[
            AlgorithmDomain(
                name="algorithm",
                status=JobStatus.CREATED,
                result=None,
                config_data=RegisteredDataDomain(registered_id="algorithm", data=ArbitraryDataDomain()),
            )
        ],
        metrics=[
            MetricDomain(
                name="metric",
                status=JobStatus.CREATED,
                result=None,
                config_data=RegisteredDataDomain(registered_id="metric", data=ArbitraryDataDomain()),
            )
        ],
        plots=[
            PlotDomain(
                name="plot",
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
        metric_registry = ArbitraryDataRegistry[IMetric]("metric")
        feature_registry = ArbitraryDataRegistry[IFeature]("feature")
        algorithm_registry = ArbitraryDataRegistry[IAlgorithm[IBackend]]("algorithm")
        plot_registry = ArbitraryDataRegistry[IPlot[Any]]("plot")

        feature_registry.register("feature", MockFeature)
        metric_registry.register("metric", MockMetric)
        algorithm_registry.register("algorithm", MockAlgorithm)
        plot_registry.register("plot", MockPlot)

        feature_mapper = FeatureMapper(feature_registry)
        metric_mapper = MetricMapper(metric_registry)
        algorithm_mapper = AlgorithmMapper(algorithm_registry)
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
        exp: Result[BenchmarkUserModel, UnknownIdError | ValidationError],
    ) -> None:
        r = BenchmarkMapper(
            mappers[0],
            mappers[1],
            mappers[2],
            mappers[3],
        ).to_user_model(benchmark_domain)
        assert type(r) is type(exp)
        assert r.unwrap() == exp.unwrap()
