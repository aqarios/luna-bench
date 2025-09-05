from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import BenchmarkStatus, SolveJobConfigDomain
from luna_bench._internal.domain_models.solve_job_result_domain import SolveJobResultDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError

if TYPE_CHECKING:
    from luna_bench._internal.dao import StorageTransaction

_result_obj = SolveJobResultDomain(meta_data=(SolveJobResultDomain.SolveJobResultMetadata(something="xD")))
_result_obj.solution = b"abc"


class TestSolveJobDAO:
    _saved_solvejob_domain: SolveJobConfigDomain

    @pytest.fixture()
    @staticmethod
    def setup_transaction(empty_transaction: StorageTransaction) -> StorageTransaction:
        """Provide a transaction fixture with a default model for testing the ModelDAOs."""
        empty_transaction.benchmark.create(benchmark_name="existing")
        TestSolveJobDAO._saved_solvejob_domain = empty_transaction.solve_job.add_solvejob(
            benchmark_name="existing",
            solve_job_name="existing",
            solve_job_config=SolveJobConfigDomain.SolveJobConfig(something="xD"),
        ).unwrap()

        return empty_transaction

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "exp"),
        [
            (
                "existing",
                "non-existing",
                Success(
                    SolveJobConfigDomain(
                        id=2,
                        name="non-existing",
                        status=BenchmarkStatus.CREATED,
                        result=None,
                        config_data=SolveJobConfigDomain.SolveJobConfig(something="xD"),
                    )
                ),
            ),
            ("existing", "existing", Failure(DataNotUniqueError())),
            ("non-existing", "non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_add_solvejob(
        setup_transaction: StorageTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.solve_job.add_solvejob(
            benchmark_name, metric_name, SolveJobConfigDomain.SolveJobConfig(something="xD")
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert len(setup_transaction.benchmark.load(benchmark_name).unwrap().solve_jobs) == 2
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
    def test_load_solvejob(
        setup_transaction: StorageTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.solve_job.load(benchmark_name, metric_name)
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == TestSolveJobDAO._saved_solvejob_domain
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
    def test_remove_solvejob(
        setup_transaction: StorageTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.solve_job.remove_solvejob(benchmark_name, metric_name)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert len(setup_transaction.benchmark.load(benchmark_name).unwrap().solve_jobs) == 0
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
    def test_update_solvejob(
        setup_transaction: StorageTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.solve_job.update_solvejob(
            benchmark_name, metric_name, SolveJobConfigDomain.SolveJobConfig(something="xD2")
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert (
                setup_transaction.benchmark.load(benchmark_name).unwrap().solve_jobs[0].status
                == BenchmarkStatus.CREATED
            )
            assert (
                setup_transaction.benchmark.load(benchmark_name).unwrap().solve_jobs[0].config_data.something == "xD2"
            )
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
        setup_transaction: StorageTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.solve_job.update_solvejob_status(benchmark_name, metric_name, BenchmarkStatus.DONE)
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert (
                setup_transaction.benchmark.load(benchmark_name).unwrap().solve_jobs[0].status == BenchmarkStatus.DONE
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
        setup_transaction: StorageTransaction,
        benchmark_name: str,
        metric_name: str,
        result: SolveJobResultDomain,
        exp: Result,
    ):
        set_result = setup_transaction.solve_job.set_result_solvejob(benchmark_name, metric_name, result)
        assert type(set_result) is type(exp)
        if is_successful(exp):
            assert setup_transaction.solve_job.load(benchmark_name, metric_name).unwrap().result == result
        else:
            assert isinstance(set_result.failure(), type(exp.failure()))

        remove = setup_transaction.solve_job.remove_result_solvejob(benchmark_name, metric_name)
        assert type(remove) is type(exp)
        if is_successful(exp):
            assert setup_transaction.solve_job.load(benchmark_name, metric_name).unwrap().result is None
        else:
            assert isinstance(remove.failure(), type(exp.failure()))
