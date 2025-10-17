from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import FeatureDomain, FeatureResultDomain, RegisteredDataDomain
from luna_bench._internal.interfaces import IFeature
from luna_bench._internal.mappers.mixins.model_list_mixin import ModelListMixin
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.user_models.feature_result_usermodel import FeatureResultUserModel
from luna_bench._internal.user_models.feature_usermodel import FeatureUserModel
from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class FeatureMapper(ModelListMixin[FeatureDomain, FeatureUserModel]):
    def __init__(
        self,
        feature_registry: PydanticRegistry[IFeature, RegisteredDataDomain],
    ) -> None:
        self._feature_registry = feature_registry

    @staticmethod
    def result_to_user_model(result: FeatureResultDomain) -> FeatureResultUserModel:
        return FeatureResultUserModel.model_construct(
            processing_time_ms=result.processing_time_ms,
            model_name=result.model_name,
            status=result.status,
            error=result.error,
            result=result.result.model_dump() if result.result else None,
        )

    @staticmethod
    def result_to_user_model_dict(results: dict[str, FeatureResultDomain]) -> dict[str, FeatureResultUserModel]:
        return {k: FeatureMapper.result_to_user_model(result) for k, result in results.items()}

    def to_user_model(
        self,
        domain: FeatureDomain,
    ) -> Result[FeatureUserModel, UnknownIdError | ValidationError]:
        """
        Convert the feature domain to the user model.

        Parameters
        ----------
        feature_domain: FeatureDomain
            The model to convert.

        Returns
        -------
        Result[FeatureUserModel, UnknownIdError | ValidationError]
            Successful conversion: The user model. Otherwise, an exception.

        """
        user_config: Result[IFeature, UnknownIdError | ValidationError] = (
            self._feature_registry.from_domain_to_user_model(domain.config_data)
        )
        if not is_successful(user_config):  # pragma: no cover
            return Failure(user_config.failure())

        return Success(
            FeatureUserModel.model_construct(
                name=domain.name,
                status=domain.status,
                feature=user_config.unwrap(),
                results=self.result_to_user_model_dict(domain.results),
            )
        )
