from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend
from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import BenchmarkDomain, RegisteredDataDomain
from luna_bench._internal.interfaces.feature_i import IFeature
from luna_bench._internal.interfaces.metric_i import IMetric
from luna_bench._internal.interfaces.plot_i import IPlot
from luna_bench._internal.mappers.algorithm_mapper import AlgorithmMapper
from luna_bench._internal.mappers.metric_mapper import MetricMapper
from luna_bench._internal.mappers.plot_mapper import PlotMapper
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.user_models import (
    AlgorithmUserModel,
    BenchmarkUserModel,
    FeatureUserModel,
    MetricUserModel,
    ModelMetadataUserModel,
    ModelSetUserModel,
    PlotUserModel,
)
from luna_bench.errors.registry.unknown_id_error import UnknownIdError

from .feature_mapper import FeatureMapper
from .utils import MapperUtils


class BenchmarkMapper:
    @staticmethod
    def to_user_model(
        benchmark_domain: BenchmarkDomain,
        metric_registry: PydanticRegistry[IMetric, RegisteredDataDomain],
        feature_registry: PydanticRegistry[IFeature, RegisteredDataDomain],
        algorithm_registry: PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain],
        plot_registry: PydanticRegistry[IPlot, RegisteredDataDomain],
    ) -> Result[BenchmarkUserModel, UnknownIdError | ValidationError]:
        features: Result[list[FeatureUserModel], UnknownIdError | ValidationError] = MapperUtils.to_user_model_list(
            benchmark_domain.features, feature_registry, FeatureMapper.to_user_model
        )

        if not is_successful(features):
            return Failure(features.failure())

        metrics: Result[list[MetricUserModel], UnknownIdError | ValidationError] = MapperUtils.to_user_model_list(
            benchmark_domain.metrics, metric_registry, MetricMapper.to_user_model
        )

        if not is_successful(metrics):
            return Failure(metrics.failure())

        algorithms: Result[list[AlgorithmUserModel], UnknownIdError | ValidationError] = MapperUtils.to_user_model_list(
            benchmark_domain.algorithms, algorithm_registry, AlgorithmMapper.to_user_model
        )

        if not is_successful(algorithms):
            return Failure(algorithms.failure())

        plots: Result[list[PlotUserModel], UnknownIdError | ValidationError] = MapperUtils.to_user_model_list(
            benchmark_domain.plots, plot_registry, PlotMapper.to_user_model
        )

        if not is_successful(plots):
            return Failure(plots.failure())

        return Success(
            BenchmarkUserModel.model_construct(
                name=benchmark_domain.name,
                modelset=ModelSetUserModel(
                    id=benchmark_domain.modelset.id,
                    name=benchmark_domain.modelset.name,
                    models=[
                        ModelMetadataUserModel.model_validate_json(m.model_dump_json(exclude={"model"}))
                        for m in benchmark_domain.modelset.models
                    ],
                )
                if benchmark_domain.modelset
                else None,
                features=features.unwrap(),
                metrics=metrics.unwrap(),
                algorithms=algorithms.unwrap(),
                plots=plots.unwrap(),
            )
        )

    @staticmethod
    def return_to_user_model[E](
        result: Result[BenchmarkDomain, E],
        metric_registry: PydanticRegistry[IMetric, RegisteredDataDomain],
        feature_registry: PydanticRegistry[IFeature, RegisteredDataDomain],
        algorithm_registry: PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain],
        plot_registry: PydanticRegistry[IPlot, RegisteredDataDomain],
    ) -> Result[BenchmarkUserModel, E | UnknownIdError | ValidationError]:
        if not is_successful(result):
            return Failure(result.failure())
        benchmark_domain: BenchmarkDomain = result.unwrap()
        return BenchmarkMapper.to_user_model(
            benchmark_domain, metric_registry, feature_registry, algorithm_registry, plot_registry
        )
