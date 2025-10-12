from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from luna_quantum.solve.interfaces.backend_i import IBackend
from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import BenchmarkDomain, RegisteredDataDomain
from luna_bench._internal.interfaces.feature_i import IFeature
from luna_bench._internal.interfaces.metric_i import IMetric
from luna_bench._internal.interfaces.plot_i import IPlot
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


class BenchmarkMapper:
    @staticmethod
    def to_user_model(
        benchmark_domain: BenchmarkDomain,
        metric_registry: PydanticRegistry[IMetric, RegisteredDataDomain],
        feature_registry: PydanticRegistry[IFeature, RegisteredDataDomain],
        algorithm_registry: PydanticRegistry[IAlgorithm[IBackend], RegisteredDataDomain],
        plot_registry: PydanticRegistry[IPlot, RegisteredDataDomain],
    ) -> Result[BenchmarkUserModel, UnknownIdError | ValidationError]:
        features: list[FeatureUserModel] = []
        metrics: list[MetricUserModel] = []
        algorithms: list[AlgorithmUserModel] = []
        plots: list[PlotUserModel] = []

        for feature in benchmark_domain.features:
            result_feature: Result[IFeature, UnknownIdError | ValidationError] = (
                feature_registry.from_domain_to_user_model(feature.config_data)
            )
            if not is_successful(result_feature):  # pragma: no cover
                return Failure(result_feature.failure())
            features.append(
                FeatureUserModel.model_construct(
                    name=feature.name,
                    status=feature.status,
                    feature=result_feature.unwrap(),
                    results=FeatureMapper.result_to_user_model_dict(feature.results),
                )
            )

        for metric in benchmark_domain.metrics:
            result_metric: Result[IMetric, UnknownIdError | ValidationError] = (
                metric_registry.from_domain_to_user_model(metric.config_data)
            )
            if not is_successful(result_metric):  # pragma: no cover
                return Failure(result_metric.failure())
            metrics.append(
                MetricUserModel.model_construct(name=metric.name, status=metric.status, metric=result_metric.unwrap())
            )

        for algorithm in benchmark_domain.algorithms:
            result_algorithm: Result[IAlgorithm[IBackend], UnknownIdError | ValidationError] = (
                algorithm_registry.from_domain_to_user_model(algorithm.config_data)
            )
            if not is_successful(result_algorithm):  # pragma: no cover
                return Failure(result_algorithm.failure())
            algorithms.append(
                AlgorithmUserModel.model_construct(
                    name=algorithm.name, status=algorithm.status, algorithm=result_algorithm.unwrap()
                )
            )

        for plot in benchmark_domain.plots:
            result_plot: Result[IPlot, UnknownIdError | ValidationError] = plot_registry.from_domain_to_user_model(
                plot.config_data
            )
            if not is_successful(result_plot):  # pragma: no cover
                return Failure(result_plot.failure())
            plots.append(PlotUserModel.model_construct(name=plot.name, status=plot.status, plot=result_plot.unwrap()))

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
                features=features,
                metrics=metrics,
                algorithms=algorithms,
                plots=plots,
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
