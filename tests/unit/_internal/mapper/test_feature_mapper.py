import pytest

from luna_bench._internal.domain_models.feature_result_domain import FeatureResultDomain
from luna_bench._internal.mappers.feature_mapper import FeatureMapper
from luna_bench.entities.enums.job_status_enum import JobStatus
from luna_bench.entities.feature_result_entity import FeatureResultEntity
from luna_bench.types import FeatureResult


class TestFeatureMapper:
    @pytest.mark.parametrize(
        ("feature_domain", "exp"),
        [
            (
                FeatureResultDomain.model_construct(
                    processing_time_ms=1,
                    model_name="model",
                    status=JobStatus.CREATED,
                    error=None,
                    result=FeatureResult.model_construct(something="xD"),  # type: ignore[call-arg] # Fake data
                ),
                FeatureResultEntity.model_construct(
                    processing_time_ms=1,
                    model_name="model",
                    status=JobStatus.CREATED,
                    error=None,
                    result=FeatureResult.model_construct(something="xD"),  # type: ignore[call-arg] # Fake data
                ),
            ),
            (
                FeatureResultDomain.model_construct(
                    processing_time_ms=1,
                    model_name="model",
                    status=JobStatus.FAILED,
                    error="An error msg",
                    result=None,
                ),
                FeatureResultEntity.model_construct(
                    processing_time_ms=1,
                    model_name="model",
                    status=JobStatus.FAILED,
                    error="An error msg",
                    result=None,
                ),
            ),
        ],
    )
    def test_feature_mapper(self, feature_domain: FeatureResultDomain, exp: FeatureResultEntity) -> None:
        assert FeatureMapper.result_to_user_model(feature_domain) == exp

    @pytest.mark.parametrize(
        ("feature_domain_dict", "exp"),
        [
            (
                {
                    "model": FeatureResultDomain.model_construct(
                        processing_time_ms=1,
                        model_name="model",
                        status=JobStatus.CREATED,
                        error=None,
                        result=FeatureResult.model_construct(something="xD"),  # type: ignore[call-arg]
                    )
                },
                {
                    "model": FeatureResultEntity.model_construct(
                        processing_time_ms=1,
                        model_name="model",
                        status=JobStatus.CREATED,
                        error=None,
                        result=FeatureResult.model_construct(something="xD"),  # type: ignore[call-arg]
                    )
                },
            ),
            (
                {
                    "model": FeatureResultDomain.model_construct(
                        processing_time_ms=1,
                        model_name="model",
                        status=JobStatus.FAILED,
                        error="An error msg",
                        result=None,
                    )
                },
                {
                    "model": FeatureResultEntity.model_construct(
                        processing_time_ms=1,
                        model_name="model",
                        status=JobStatus.FAILED,
                        error="An error msg",
                        result=None,
                    )
                },
            ),
        ],
    )
    def test_feature_mapper_dict(
        self, feature_domain_dict: dict[str, FeatureResultDomain], exp: dict[str, FeatureResultEntity]
    ) -> None:
        assert FeatureMapper.result_to_user_model_dict(feature_domain_dict) == exp
