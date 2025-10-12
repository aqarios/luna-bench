from luna_bench._internal.domain_models import FeatureResultDomain
from luna_bench._internal.user_models.feature_result_usermodel import FeatureResultUserModel


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
