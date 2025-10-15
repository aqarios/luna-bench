from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import AlgorithmDomain, BenchmarkStatus, JobStatus
from luna_bench._internal.domain_models.algorithm_result_domain import AlgorithmResultDomain
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.registered_data_domain import RegisteredDataDomain
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from tests.unit.fixtures.mock_config import MockConfig

if TYPE_CHECKING:
    from luna_bench._internal.dao import DaoTransaction

_result_obj = AlgorithmResultDomain(
    meta_data=(ArbitraryDataDomain.model_validate(MockConfig(something="xD").model_dump(), from_attributes=True))
)
_result_obj.solution = b"abc"


class TestAlgorithmDAO:
    _saved_algorithm_domain: AlgorithmDomain

    @pytest.fixture()
    @staticmethod
    def setup_transaction(empty_transaction: DaoTransaction) -> DaoTransaction:
        """Provide a transaction fixture with a default model for testing the ModelDAOs."""
        empty_transaction.benchmark.create(benchmark_name="existing")
        TestAlgorithmDAO._saved_algorithm_domain = empty_transaction.algorithm.add(
            benchmark_name="existing",
            algorithm_name="existing",
            registered_id="existing",
            algorithm=ArbitraryDataDomain(),
        ).unwrap()

        return empty_transaction

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "exp"),
        [
            (
                "existing",
                "non-existing",
                Success(
                    AlgorithmDomain(
                        name="non-existing",
                        status=JobStatus.CREATED,
                        result=None,
                        config_data=RegisteredDataDomain(
                            registered_id="existing",
                            data=ArbitraryDataDomain.model_validate(
                                MockConfig(something="xD").model_dump(), from_attributes=True
                            ),
                        ),
                    )
                ),
            ),
            ("existing", "existing", Failure(DataNotUniqueError())),
            ("non-existing", "non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_add_algorithm(
        setup_transaction: DaoTransaction,
        benchmark_name: str,
        metric_name: str,
        exp: Result[AlgorithmDomain, DataNotExistError | DataNotUniqueError],
    ) -> None:
        result = setup_transaction.algorithm.add(
            benchmark_name,
            metric_name,
            "existing",
            ArbitraryDataDomain.model_validate(MockConfig(something="xD").model_dump(), from_attributes=True),
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
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result[None, DataNotExistError]
    ) -> None:
        result = setup_transaction.algorithm.load(benchmark_name, metric_name)
        assert is_successful(result) == is_successful(exp)

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
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result[None, DataNotExistError]
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
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result[None, DataNotExistError]
    ) -> None:
        result = setup_transaction.algorithm.update(
            benchmark_name,
            metric_name,
            "existing2",
            ArbitraryDataDomain.model_validate(MockConfig(something="xD2").model_dump(), from_attributes=True),
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            r = setup_transaction.benchmark.load(benchmark_name).unwrap().algorithms[0]

            assert r.status == JobStatus.CREATED
            assert getattr(r.config_data.data, "something", "nope") == "xD2"
            assert r.config_data.registered_id == "existing2"
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
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result[None, DataNotExistError]
    ) -> None:
        result = setup_transaction.algorithm.update_status(benchmark_name, metric_name, BenchmarkStatus.DONE)
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert setup_transaction.benchmark.load(benchmark_name).unwrap().algorithms[0].status == JobStatus.DONE
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
        exp: Result[None, DataNotExistError],
    ) -> None:
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
