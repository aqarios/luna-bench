from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import (
    AlgorithmDomain,
    BenchmarkDomain,
    FeatureDomain,
    MetricDomain,
    PlotDomain,
)
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

from .types import ListMapper, Mapper


class BenchmarkMapper(Mapper[BenchmarkDomain, BenchmarkUserModel]):
    def __init__(
        self,
        feature_mapper: ListMapper[FeatureDomain, FeatureUserModel],
        metric_mapper: ListMapper[MetricDomain, MetricUserModel],
        algorithm_mapper: ListMapper[AlgorithmDomain, AlgorithmUserModel],
        plot_mapper: ListMapper[PlotDomain, PlotUserModel],
    ) -> None:
        self._feature_mapper = feature_mapper
        self._metric_mapper = metric_mapper
        self._algorithm_mapper = algorithm_mapper
        self._plot_mapper = plot_mapper

    def to_user_model(
        self,
        domain: BenchmarkDomain,
    ) -> Result[BenchmarkUserModel, UnknownIdError | ValidationError]:
        features: Result[list[FeatureUserModel], UnknownIdError | ValidationError] = (
            self._feature_mapper.to_user_model_list(
                domain.features,
            )
        )

        if not is_successful(features):
            return Failure(features.failure())

        metrics: Result[list[MetricUserModel], UnknownIdError | ValidationError] = (
            self._metric_mapper.to_user_model_list(
                domain.metrics,
            )
        )

        if not is_successful(metrics):
            return Failure(metrics.failure())

        algorithms: Result[list[AlgorithmUserModel], UnknownIdError | ValidationError] = (
            self._algorithm_mapper.to_user_model_list(
                domain.algorithms,
            )
        )

        if not is_successful(algorithms):
            return Failure(algorithms.failure())

        plots: Result[list[PlotUserModel], UnknownIdError | ValidationError] = self._plot_mapper.to_user_model_list(
            domain.plots,
        )

        if not is_successful(plots):
            return Failure(plots.failure())

        return Success(
            BenchmarkUserModel.model_construct(
                name=domain.name,
                modelset=ModelSetUserModel(
                    id=domain.modelset.id,
                    name=domain.modelset.name,
                    models=[
                        ModelMetadataUserModel.model_validate_json(m.model_dump_json(exclude={"model"}))
                        for m in domain.modelset.models
                    ],
                )
                if domain.modelset
                else None,
                features=features.unwrap(),
                metrics=metrics.unwrap(),
                algorithms=algorithms.unwrap(),
                plots=plots.unwrap(),
            )
        )
