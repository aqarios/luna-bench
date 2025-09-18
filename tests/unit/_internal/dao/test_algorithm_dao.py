from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import AlgorithmConfigDomain, BenchmarkStatus
from luna_bench._internal.domain_models.algorithm_result_domain import AlgorithmResultDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError

if TYPE_CHECKING:
    from luna_bench._internal.dao import DaoTransaction

_result_obj = AlgorithmResultDomain(meta_data=(AlgorithmResultDomain.AlgorithmResultMetadata(something="xD")))
_result_obj.solution = b"abc"


class TestAlgorithmDAO:
    _saved_algorithm_domain: AlgorithmConfigDomain

    @pytest.fixture()
    @staticmethod
    def setup_transaction(empty_transaction: DaoTransaction) -> DaoTransaction:
        """Provide a transaction fixture with a default model for testing the ModelDAOs."""
        empty_transaction.benchmark.create(benchmark_name="existing")
        TestAlgorithmDAO._saved_algorithm_domain = empty_transaction.algorithm.add(
            benchmark_name="existing",
            solve_job_name="existing",
            algorithm=AlgorithmConfigDomain.Algorithm(),
            backend=None,
        ).unwrap()

        return empty_transaction

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "exp"),
        [
            (
                "existing",
                "non-existing",
                Success(
                    AlgorithmConfigDomain(
                        id=2,
                        name="non-existing",
                        status=BenchmarkStatus.CREATED,
                        result=None,
                        algorithm=AlgorithmConfigDomain.Algorithm(something="xD"),
                        backend=None,
                    )
                ),
            ),
            ("existing", "existing", Failure(DataNotUniqueError())),
            ("non-existing", "non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_add_algorithm(
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.algorithm.add(
            benchmark_name, metric_name, AlgorithmConfigDomain.Algorithm(something="xD")
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert len(setup_transaction.benchmark.load(benchmark_name).unwrap().algorithms) == 2
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "exp"),
        [
            (
                "existing",
                "existing",
                Success(None),
            ),
            ("existing", "non-existing", Failure(DataNotExistError())),
            ("non-existing", "non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_load_algorithm(
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.algorithm.load(benchmark_name, metric_name)
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == TestAlgorithmDAO._saved_algorithm_domain
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "exp"),
        [
            (
                "existing",
                "existing",
                Success(None),
            ),
            ("non-existing", "existing", Failure(DataNotExistError())),
            ("existing", "non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_remove_algorithm(
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.algorithm.remove(benchmark_name, metric_name)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert len(setup_transaction.benchmark.load(benchmark_name).unwrap().algorithms) == 0
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "exp"),
        [
            (
                "existing",
                "existing",
                Success(None),
            ),
            ("non-existing", "existing", Failure(DataNotExistError())),
            ("existing", "non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_update_algorithm(
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.algorithm.update(
            benchmark_name, metric_name, AlgorithmConfigDomain.Algorithm(something="xD2")
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert (
                setup_transaction.benchmark.load(benchmark_name).unwrap().algorithms[0].status
                == BenchmarkStatus.CREATED
            )
            assert setup_transaction.benchmark.load(benchmark_name).unwrap().algorithms[0].algorithm.something == "xD2"
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "exp"),
        [
            (
                "existing",
                "existing",
                Success(None),
            ),
            ("non-existing", "existing", Failure(DataNotExistError())),
            ("existing", "non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_update_modelmetric_status(
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.algorithm.update_status(benchmark_name, metric_name, BenchmarkStatus.DONE)
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert (
                setup_transaction.benchmark.load(benchmark_name).unwrap().algorithms[0].status == BenchmarkStatus.DONE
            )
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "result", "exp"),
        [
            (
                "existing",
                "existing",
                _result_obj,
                Success(None),
            ),
            ("non-existing", "existing", _result_obj, Failure(DataNotExistError())),
            ("existing", "non-existing", _result_obj, Failure(DataNotExistError())),
        ],
    )
    def test_result_storage(
        self,
        setup_transaction: DaoTransaction,
        benchmark_name: str,
        metric_name: str,
        result: AlgorithmResultDomain,
        exp: Result,
    ):
        set_result = setup_transaction.algorithm.set_result(benchmark_name, metric_name, result)
        assert type(set_result) is type(exp)
        if is_successful(exp):
            a = setup_transaction.algorithm.load(benchmark_name, metric_name)
            assert a.unwrap().result == result

        else:
            assert isinstance(set_result.failure(), type(exp.failure()))

        remove = setup_transaction.algorithm.remove_result(benchmark_name, metric_name)
        assert type(remove) is type(exp)
        if is_successful(exp):
            assert setup_transaction.algorithm.load(benchmark_name, metric_name).unwrap().result is None
        else:
            assert isinstance(remove.failure(), type(exp.failure()))
