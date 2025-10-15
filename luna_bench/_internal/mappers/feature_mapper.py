from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import FeatureDomain, FeatureResultDomain, RegisteredDataDomain
from luna_bench._internal.interfaces import IFeature
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.user_models.feature_result_usermodel import FeatureResultUserModel
from luna_bench._internal.user_models.feature_usermodel import FeatureUserModel
from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class FeatureMapper:
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

    @staticmethod
    def to_user_model(
        feature_domain: FeatureDomain, feature_registry: PydanticRegistry[IFeature, RegisteredDataDomain]
    ) -> Result[FeatureUserModel, UnknownIdError | ValidationError]:
        """
        Convert the feature domain to the user model.

        Parameters
        ----------
        feature_domain: FeatureDomain
            The model to convert.
        feature_registry: PydanticRegistry[IFeature, RegisteredDataDomain]
            The registry to use for the conversion.

        Returns
        -------
        Result[FeatureUserModel, UnknownIdError | ValidationError]
            Successful conversion: The user model. Otherwise, an exception.

        """
        user_config: Result[IFeature, UnknownIdError | ValidationError] = feature_registry.from_domain_to_user_model(
            feature_domain.config_data
        )
        if not is_successful(user_config):  # pragma: no cover
            return Failure(user_config.failure())

        return Success(
            FeatureUserModel.model_construct(
                name=feature_domain.name,
                status=feature_domain.status,
                feature=user_config.unwrap(),
                results=FeatureMapper.result_to_user_model_dict(feature_domain.results),
            )
        )
