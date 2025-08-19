from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import BenchmarkDomain, BenchmarkStatus
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError

if TYPE_CHECKING:
    from luna_bench._internal.dao import StorageTransaction
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


class TestBenchmarkDAO:
    @pytest.fixture()
    @staticmethod
    def setup_transaction(empty_transaction: StorageTransaction) -> StorageTransaction:
        """Provide a transaction fixture with a default model for testing the ModelDAOs."""
        empty_transaction.benchmark.create(benchmark_name="existing")
        empty_transaction.modelset.create(modelset_name="existing")
        return empty_transaction

    @pytest.mark.parametrize(
        ("name", "exp"),
        [
            (
                "non-existing",
                Success(
                    BenchmarkDomain(
                        id=2,
                        name="non-existing",
                        status=BenchmarkStatus.CREATED,
                        modelset=None,
                        modelmetrics=[],
                        solve_jobs=[],
                        metrics=[],
                        plots=[],
                    )
                ),
            ),
            ("existing", Failure(DataNotUniqueError())),
            ("Existing", Failure(DataNotUniqueError())),
        ],
    )
    @staticmethod
    def test_create(setup_transaction: StorageTransaction, name: str, exp: Result) -> None:
        result: Result[BenchmarkDomain, DataNotUniqueError | UnknownLunaBenchError] = (
            setup_transaction.benchmark.create(name)
        )

        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("name", "exp"),
        [
            (
                "existing",
                Success(
                    BenchmarkDomain(
                        id=1,
                        name="existing",
                        status=BenchmarkStatus.CREATED,
                        modelset=None,
                        modelmetrics=[],
                        solve_jobs=[],
                        metrics=[],
                        plots=[],
                    )
                ),
            ),
            ("non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_load(setup_transaction: StorageTransaction, name: str, exp: Result) -> None:
        result: Result[BenchmarkDomain, DataNotExistError | UnknownLunaBenchError] = setup_transaction.benchmark.load(
            name
        )

        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("name", "exp"),
        [
            (
                "existing",
                Success(None),
            ),
            ("non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_delete(setup_transaction: StorageTransaction, name: str, exp: Result) -> None:
        result: Result[None, DataNotExistError | UnknownLunaBenchError] = setup_transaction.benchmark.delete(name)

        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @staticmethod
    def test_load_all(setup_transaction: StorageTransaction) -> None:
        result: Result[list[BenchmarkDomain], UnknownLunaBenchError] = setup_transaction.benchmark.load_all()

        benchmarks = result.unwrap()
        assert len(benchmarks) == 1
        assert benchmarks[0].name == "existing"

        setup_transaction.benchmark.delete("existing")
        result = setup_transaction.benchmark.load_all()

        benchmarks = result.unwrap()
        assert len(benchmarks) == 0

    @pytest.mark.parametrize(
        ("name", "modelset_name", "exp"),
        [
            (
                "existing",
                "existing",
                Success(None),
            ),
            ("existing", "non-existing", Failure(DataNotExistError())),
            ("non-existing", "existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_add_modelset(setup_transaction: StorageTransaction, name: str, modelset_name: str, exp: Result) -> None:
        result: Result[None, DataNotExistError | UnknownLunaBenchError] = setup_transaction.benchmark.set_modelset(
            name, modelset_name
        )

        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()

            assert setup_transaction.benchmark.load(name).unwrap().modelset.name == modelset_name
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_add_name", "benchmark_remove_name", "exp"),
        [
            (
                "existing",
                "existing",
                Success(None),
            ),
            ("existing", "non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_remove_modelset(
        setup_transaction: StorageTransaction, benchmark_add_name: str, benchmark_remove_name: str, exp: Result
    ) -> None:
        setup_transaction.benchmark.set_modelset(benchmark_add_name, "existing")
        result: Result[None, DataNotExistError | UnknownLunaBenchError] = setup_transaction.benchmark.remove_modelset(
            benchmark_remove_name
        )

        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))
