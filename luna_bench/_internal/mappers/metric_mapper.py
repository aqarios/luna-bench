from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import MetricDomain, MetricResultDomain, RegisteredDataDomain
from luna_bench._internal.mappers.mixins.model_list_mixin import ModelListMixin
from luna_bench._internal.registries import PydanticRegistry
from luna_bench.base_components import BaseMetric
from luna_bench.entities import MetricEntity, MetricResultEntity
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.types import MetricResult


class MetricMapper(ModelListMixin[MetricDomain, MetricEntity]):
    def __init__(
        self,
        metric_registry: PydanticRegistry[BaseMetric, RegisteredDataDomain],
    ) -> None:
        self._metric_registry = metric_registry

    @staticmethod
    def result_to_user_model(result: MetricResultDomain) -> MetricResultEntity:
        return MetricResultEntity.model_construct(
            processing_time_ms=result.processing_time_ms,
            model_name=result.model_name,
            algorithm_name=result.algorithm_name,
            status=result.status,
            error=result.error,
            result=MetricResult.model_construct(**result.result.model_dump()) if result.result else None,
        )

    @staticmethod
    def result_to_user_model_dict(
        results: dict[tuple[str, str], MetricResultDomain],
    ) -> dict[tuple[str, str], MetricResultEntity]:
        return {(k, m): MetricMapper.result_to_user_model(result) for (k, m), result in results.items()}

    def to_user_model(
        self,
        domain: MetricDomain,
    ) -> Result[MetricEntity, UnknownIdError | ValidationError]:
        """
        Convert the algorithm domain to the user model.

        Parameters
        ----------
        metric_domain: MetricDomain
            The model to convert.

        Returns
        -------
        Result[MetricEntity, UnknownIdError | ValidationError]
            Successful conversion: The user model. Otherwise, an exception.

        """
        user_config: Result[BaseMetric, UnknownIdError | ValidationError] = (
            self._metric_registry.from_domain_to_user_model(domain.config_data)
        )
        if not is_successful(user_config):  # pragma: no cover
            return Failure(user_config.failure())

        return Success(
            MetricEntity.model_construct(
                name=domain.name,
                status=domain.status,
                metric=user_config.unwrap(),
                results=self.result_to_user_model_dict(domain.results),
            )
        )
