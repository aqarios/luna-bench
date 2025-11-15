from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.user_models import BenchmarkUserModel
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from tests.unit._internal.usecases.benchmark.test_utils import _full_benchmark_usermodel

if TYPE_CHECKING:
    from pydantic import ValidationError

    from luna_bench._internal.usecases.usecase_container import UsecaseContainer
    from luna_bench.errors.registry.unknown_id_error import UnknownIdError
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


def _empty_benchmark(name: str) -> BenchmarkUserModel:
    return BenchmarkUserModel(
        name=name,
        modelset=None,
        features=[],
        algorithms=[],
        metrics=[],
        plots=[],
    )


class TestBenchmark:
    @pytest.mark.parametrize(
        ("benchmark_name", "exp"),
        [
            ("existing", Failure(DataNotUniqueError())),
            ("non-existing", Success(_empty_benchmark("non-existing"))),
        ],
    )
    def test_create(
        self,
        usecase: UsecaseContainer,
        benchmark_name: str,
        exp: Result[BenchmarkUserModel, DataNotUniqueError | UnknownLunaBenchError | UnknownIdError | ValidationError],
    ) -> None:
        result: Result[
            BenchmarkUserModel, DataNotUniqueError | UnknownLunaBenchError | UnknownIdError | ValidationError
        ] = usecase.benchmark_create_uc()(benchmark_name)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "exp"),
        [
            ("existing", Success(None)),
            ("non-existing", Failure(DataNotExistError())),
        ],
    )
    def test_delete(
        self,
        usecase: UsecaseContainer,
        benchmark_name: str,
        exp: Result[None, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        result: Result[None, DataNotExistError | UnknownLunaBenchError] = usecase.benchmark_delete_uc()(benchmark_name)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "exp"),
        [
            ("existing", Success(_full_benchmark_usermodel("existing"))),
            ("non-existing", Failure(DataNotExistError())),
        ],
    )
    def test_load(
        self,
        usecase: UsecaseContainer,
        benchmark_name: str,
        exp: Result[BenchmarkUserModel, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        result: Result[
            BenchmarkUserModel, DataNotExistError | UnknownLunaBenchError | UnknownIdError | ValidationError
        ] = usecase.benchmark_load_uc()(benchmark_name)

        if is_successful(exp):
            assert result.unwrap().model_dump_json() == exp.unwrap().model_dump_json()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("exp"),
        [
            (Success([_full_benchmark_usermodel("existing")])),
        ],
    )
    def test_load_all(
        self,
        usecase: UsecaseContainer,
        exp: Result[list[BenchmarkUserModel], DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        result: Result[list[BenchmarkUserModel], UnknownLunaBenchError | UnknownIdError | ValidationError] = (
            usecase.benchmark_load_all_uc()()
        )

        if is_successful(exp):
            assert [r.model_dump_json() for r in result.unwrap()] == [r.model_dump_json() for r in exp.unwrap()]
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("bench_name", "modelset_name", "exp"),
        [
            ("existing", "new", Success(None)),
            ("non-existing", "existing", Failure(DataNotExistError())),
            ("existing", "non-existing", Failure(DataNotExistError())),
        ],
    )
    def test_set_modelset(
        self,
        usecase: UsecaseContainer,
        bench_name: str,
        modelset_name: str,
        exp: Result[None, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        assert is_successful(usecase.modelset_create_uc()(modelset_name="new"))

        result: Result[None, DataNotExistError | UnknownLunaBenchError] = usecase.benchmark_set_modelset_uc()(
            benchmark_name=bench_name, modelset_name=modelset_name
        )

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert usecase.benchmark_load_uc()(benchmark_name="existing").unwrap().modelset is not None
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("bench_name", "exp"),
        [("existing", Success(None)), ("non-existing", Failure(DataNotExistError()))],
    )
    def test_remove_modelset(
        self,
        usecase: UsecaseContainer,
        bench_name: str,
        exp: Result[None, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        result: Result[None, DataNotExistError | UnknownLunaBenchError] = usecase.benchmark_remove_modelset_uc()(
            bench_name
        )

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert usecase.benchmark_load_uc()(benchmark_name="existing").unwrap().modelset is None
        else:
            assert isinstance(result.failure(), type(exp.failure()))
