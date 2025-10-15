from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from luna_quantum.solve.interfaces.algorithm_i import IAlgorithm
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.user_models import AlgorithmUserModel, BenchmarkUserModel
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from tests.unit.fixtures.mock_components import MockAlgorithm, UnregisteredAlgorithm

if TYPE_CHECKING:
    from luna_quantum.solve.interfaces.backend_i import IBackend
    from pydantic import ValidationError

    from luna_bench._internal.usecases.usecase_container import UsecaseContainer
    from luna_bench.errors.registry.unknown_id_error import UnknownIdError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


def _empty_algorithm(name: str, algorithm: IAlgorithm[IBackend]) -> AlgorithmUserModel:
    return AlgorithmUserModel(
        name=name,
        status=JobStatus.CREATED,
        algorithm=algorithm,
    )


class TestAlgorithm:
    @pytest.fixture()
    @staticmethod
    def default_usecase(usecase: UsecaseContainer) -> UsecaseContainer:
        create_default: Result[
            BenchmarkUserModel, DataNotUniqueError | UnknownLunaBenchError | UnknownIdError | ValidationError
        ] = usecase.benchmark_create_uc()(benchmark_name="existing")
        assert is_successful(create_default)
        create_default_algorithm = usecase.benchmark_add_algorithm_uc()(
            benchmark_name="existing", name="existing", algorithm=MockAlgorithm()
        )
        assert is_successful(create_default_algorithm)

        return usecase

    @pytest.mark.parametrize(
        ("benchmark_name", "algorithm_name", "algorithm", "exp"),
        [
            ("non-existing", "existing", MockAlgorithm(), Failure(DataNotExistError())),
            ("existing", "existing", MockAlgorithm(), Failure(DataNotUniqueError())),
            ("existing", "non-existing", UnregisteredAlgorithm(), Failure(UnknownComponentError("", IAlgorithm))),
            ("existing", "non-existing", MockAlgorithm(), Success(_empty_algorithm("non-existing", MockAlgorithm()))),
        ],
    )
    def test_add(
        self,
        default_usecase: UsecaseContainer,
        benchmark_name: str,
        algorithm_name: str,
        algorithm: IAlgorithm[IBackend],
        exp: Result[
            AlgorithmUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ],
    ) -> None:
        result: Result[
            AlgorithmUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ] = default_usecase.benchmark_add_algorithm_uc()(benchmark_name, algorithm_name, algorithm)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "algorithm_name", "exp"),
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
        algorithm_name: str,
        exp: Result[
            AlgorithmUserModel,
            DataNotUniqueError
            | DataNotExistError
            | UnknownLunaBenchError
            | UnknownComponentError
            | UnknownIdError
            | ValidationError,
        ],
    ) -> None:
        result: Result[None, DataNotExistError | UnknownLunaBenchError] = (
            default_usecase.benchmark_remove_algorithm_uc()(benchmark_name, algorithm_name)
        )

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))
