from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import BenchmarkStatus, MetricConfigDomain, MetricResultDomain
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError

if TYPE_CHECKING:
    from luna_bench._internal.dao import DaoTransaction


class TestMetricDAO:
    _saved_metric_domain: MetricConfigDomain

    @pytest.fixture()
    @staticmethod
    def setup_transaction(empty_transaction: DaoTransaction) -> DaoTransaction:
        """Provide a transaction fixture with a default model for testing the ModelDAOs."""
        empty_transaction.benchmark.create(benchmark_name="existing")
        TestMetricDAO._saved_metric_domain = empty_transaction.metric.add(
            benchmark_name="existing",
            metric_name="existing",
            metric_config=MetricConfigDomain.MetricConfig(something="xD"),
        ).unwrap()

        return empty_transaction

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "exp"),
        [
            (
                "existing",
                "non-existing",
                Success(
                    MetricConfigDomain(
                        id=2,
                        name="non-existing",
                        status=BenchmarkStatus.CREATED,
                        result=None,
                        config_data=MetricConfigDomain.MetricConfig(something="xD"),
                    )
                ),
            ),
            ("existing", "existing", Failure(DataNotUniqueError())),
            ("non-existing", "non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_add_metric(setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result) -> None:
        result = setup_transaction.metric.add(
            benchmark_name, metric_name, MetricConfigDomain.MetricConfig(something="xD")
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert len(setup_transaction.benchmark.load(benchmark_name).unwrap().metrics) == 2
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
    def test_load_metric(setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result) -> None:
        result = setup_transaction.metric.load(benchmark_name, metric_name)
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == TestMetricDAO._saved_metric_domain
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
    def test_remove_metric(
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.metric.remove(benchmark_name, metric_name)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert len(setup_transaction.benchmark.load(benchmark_name).unwrap().metrics) == 0
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
    def test_update_metric(
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.metric.update(
            benchmark_name, metric_name, MetricConfigDomain.MetricConfig(something="xD2")
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert (
                setup_transaction.benchmark.load(benchmark_name).unwrap().metrics[0].status == BenchmarkStatus.CREATED
            )
            assert setup_transaction.benchmark.load(benchmark_name).unwrap().metrics[0].config_data.something == "xD2"
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
    def test_update_metric_status(
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.metric.update_metric_status(benchmark_name, metric_name, BenchmarkStatus.DONE)
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert setup_transaction.benchmark.load(benchmark_name).unwrap().metrics[0].status == BenchmarkStatus.DONE
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "result", "exp"),
        [
            (
                "existing",
                "existing",
                MetricResultDomain(v="result"),
                Success(None),
            ),
            ("non-existing", "existing", MetricResultDomain(v="result"), Failure(DataNotExistError())),
            ("existing", "non-existing", MetricResultDomain(v="result"), Failure(DataNotExistError())),
        ],
    )
    def test_result_storage(
        self,
        setup_transaction: DaoTransaction,
        benchmark_name: str,
        metric_name: str,
        result: MetricResultDomain,
        exp: Result,
    ):
        set_result = setup_transaction.metric.set_result(benchmark_name, metric_name, result)
        assert type(set_result) is type(exp)
        if is_successful(exp):
            assert setup_transaction.metric.load(benchmark_name, metric_name).unwrap().result == result
        else:
            assert isinstance(set_result.failure(), type(exp.failure()))

        remove = setup_transaction.metric.remove_result(benchmark_name, metric_name)
        assert type(remove) is type(exp)
        if is_successful(exp):
            assert setup_transaction.metric.load(benchmark_name, metric_name).unwrap().result is None
        else:
            assert isinstance(remove.failure(), type(exp.failure()))
