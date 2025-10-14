from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.interfaces.feature_i import IFeature
from luna_bench._internal.user_models import BenchmarkUserModel, FeatureUserModel
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from tests.unit.fixtures.mock_components import MockFeature, UnregisteredFeature

if TYPE_CHECKING:
    from pydantic import ValidationError

    from luna_bench._internal.usecases.usecase_container import UsecaseContainer
    from luna_bench.errors.registry.unknown_id_error import UnknownIdError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


def _empty_feature(name: str, feature: IFeature) -> FeatureUserModel:
    return FeatureUserModel(
        name=name,
        status=JobStatus.CREATED,
        feature=feature,
    )


class TestFeature:
    @pytest.fixture()
    @staticmethod
    def default_usecase(usecase: UsecaseContainer) -> UsecaseContainer:
        create_default: Result[
            BenchmarkUserModel, DataNotUniqueError | UnknownLunaBenchError | UnknownIdError | ValidationError
        ] = usecase.benchmark_create_uc()(benchmark_name="existing")
        assert is_successful(create_default)
        create_default_feature = usecase.benchmark_add_feature_uc()(
            benchmark_name="existing", name="existing", feature=MockFeature()
        )
        assert is_successful(create_default_feature)

        return usecase

    @pytest.mark.parametrize(
        ("benchmark_name", "feature_name", "feature", "exp"),
        [
            ("non-existing", "existing", MockFeature(), Failure(DataNotExistError())),
            ("existing", "existing", MockFeature(), Failure(DataNotUniqueError())),
            ("existing", "non-existing", UnregisteredFeature(), Failure(UnknownComponentError("", IFeature))),
            ("existing", "non-existing", MockFeature(), Success(_empty_feature("non-existing", MockFeature()))),
        ],
    )
    def test_add(
        self,
        default_usecase: UsecaseContainer,
        benchmark_name: str,
        feature_name: str,
        feature: IFeature,
        exp: Result[
            FeatureUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ],
    ) -> None:
        result: Result[
            FeatureUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ] = default_usecase.benchmark_add_feature_uc()(benchmark_name, feature_name, feature)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "feature_name", "exp"),
        [
            ("non-existing", "existing", Failure(DataNotExistError())),
            ("existing", "non-existing", Failure(DataNotExistError())),
            ("existing", "existing", Success(None)),
        ],
    )
    def test_remove(
        self,
        default_usecase: UsecaseContainer,
        benchmark_name: str,
        feature_name: str,
        exp: Result[
            FeatureUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ],
    ) -> None:
        result: Result[None, DataNotExistError | UnknownLunaBenchError] = default_usecase.benchmark_remove_feature_uc()(
            benchmark_name, feature_name
        )

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))
