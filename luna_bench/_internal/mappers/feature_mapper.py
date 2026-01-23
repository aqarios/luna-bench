from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import FeatureDomain, FeatureResultDomain, RegisteredDataDomain
from luna_bench._internal.mappers.mixins.model_list_mixin import ModelListMixin
from luna_bench._internal.registries import PydanticRegistry
from luna_bench.base_components import BaseFeature
from luna_bench.entities.feature_entity import FeatureEntity
from luna_bench.entities.feature_result_entity import FeatureResultEntity
from luna_bench.errors.registry.unknown_id_error import UnknownIdError
from luna_bench.types import FeatureResult


class FeatureMapper(ModelListMixin[FeatureDomain, FeatureEntity]):
    def __init__(
        self,
        feature_registry: PydanticRegistry[BaseFeature, RegisteredDataDomain],
    ) -> None:
        self._feature_registry = feature_registry

    @staticmethod
    def result_to_user_model(result: FeatureResultDomain) -> FeatureResultEntity:
        return FeatureResultEntity.model_construct(
            processing_time_ms=result.processing_time_ms,
            model_name=result.model_name,
            status=result.status,
            error=result.error,
            result=FeatureResult.model_construct(**result.result.model_dump()) if result.result else None,
        )

    @staticmethod
    def result_to_user_model_dict(results: dict[str, FeatureResultDomain]) -> dict[str, FeatureResultEntity]:
        return {k: FeatureMapper.result_to_user_model(result) for k, result in results.items()}

    def to_user_model(
        self,
        domain: FeatureDomain,
    ) -> Result[FeatureEntity, UnknownIdError | ValidationError]:
        """
        Convert the feature domain to the user model.

        Parameters
        ----------
        feature_domain: FeatureDomain
            The model to convert.

        Returns
        -------
        Result[FeatureEntity, UnknownIdError | ValidationError]
            Successful conversion: The user model. Otherwise, an exception.

        """
        user_config: Result[BaseFeature, UnknownIdError | ValidationError] = (
            self._feature_registry.from_domain_to_user_model(domain.config_data)
        )
        if not is_successful(user_config):  # pragma: no cover
            return Failure(user_config.failure())

        return Success(
            FeatureEntity.model_construct(
                name=domain.name,
                status=domain.status,
                feature=user_config.unwrap(),
                results=self.result_to_user_model_dict(domain.results),
            )
        )
