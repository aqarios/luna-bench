import pytest

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.feature_result_domain import FeatureResultDomain
from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.mappers.feature_mapper import FeatureMapper
from luna_bench._internal.user_models.feature_result_usermodel import FeatureResultUserModel


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
                    result=ArbitraryDataDomain.model_construct(something="xD"),  # type: ignore[call-arg] # Fake data
                ),
                FeatureResultUserModel.model_construct(
                    processing_time_ms=1,
                    model_name="model",
                    status=JobStatus.CREATED,
                    error=None,
                    result={"something": "xD"},
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
                FeatureResultUserModel.model_construct(
                    processing_time_ms=1,
                    model_name="model",
                    status=JobStatus.FAILED,
                    error="An error msg",
                    result=None,
                ),
            ),
        ],
    )
    def test_feature_mapper(self, feature_domain: FeatureResultDomain, exp: FeatureResultUserModel) -> None:
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
                        result=ArbitraryDataDomain.model_construct(something="xD"),
                    )
                },
                {
                    "model": FeatureResultUserModel.model_construct(
                        processing_time_ms=1,
                        model_name="model",
                        status=JobStatus.CREATED,
                        error=None,
                        result={"something": "xD"},
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
                    "model": FeatureResultUserModel.model_construct(
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
        self, feature_domain_dict: dict[str, FeatureResultDomain], exp: dict[str, FeatureResultUserModel]
    ) -> None:
        assert FeatureMapper.result_to_user_model_dict(feature_domain_dict) == exp
