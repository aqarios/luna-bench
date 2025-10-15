from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import BenchmarkStatus, MetricDomain, MetricResultDomain
from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.job_status_enum import JobStatus
from luna_bench._internal.domain_models.registered_data_domain import RegisteredDataDomain
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from tests.unit.fixtures.mock_config import MockConfig

if TYPE_CHECKING:
    from luna_bench._internal.dao import DaoTransaction


class TestMetricDAO:
    _saved_metric_domain: MetricDomain

    @pytest.fixture()
    @staticmethod
    def setup_transaction(empty_transaction: DaoTransaction) -> DaoTransaction:
        """Provide a transaction fixture with a default model for testing the ModelDAOs."""
        empty_transaction.benchmark.create(benchmark_name="existing")
        TestMetricDAO._saved_metric_domain = empty_transaction.metric.add(
            benchmark_name="existing",
            metric_name="existing",
            registered_id="existing",
            metric_config=ArbitraryDataDomain.model_validate(
                MockConfig(something="xD").model_dump(), from_attributes=True
            ),
        ).unwrap()

        return empty_transaction

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "exp"),
        [
            (
                "existing",
                "non-existing",
                Success(
                    MetricDomain(
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
    def test_add_metric(
        setup_transaction: DaoTransaction,
        benchmark_name: str,
        metric_name: str,
        exp: Result[MetricDomain, DataNotExistError | DataNotUniqueError],
    ) -> None:
        result = setup_transaction.metric.add(
            benchmark_name,
            metric_name,
            "existing",
            ArbitraryDataDomain.model_validate(MockConfig(something="xD").model_dump(), from_attributes=True),
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
    def test_load_metric(
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result[None, DataNotExistError]
    ) -> None:
        result = setup_transaction.metric.load(benchmark_name, metric_name)

        assert is_successful(result) == is_successful(exp)

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
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result[None, DataNotExistError]
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
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result[None, DataNotExistError]
    ) -> None:
        result = setup_transaction.metric.update(
            benchmark_name,
            metric_name,
            "existing2",
            ArbitraryDataDomain.model_validate(MockConfig(something="xD2").model_dump(), from_attributes=True),
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            r = setup_transaction.benchmark.load(benchmark_name).unwrap().metrics[0]

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
    def test_update_metric_status(
        setup_transaction: DaoTransaction, benchmark_name: str, metric_name: str, exp: Result[None, DataNotExistError]
    ) -> None:
        result = setup_transaction.metric.update_status(benchmark_name, metric_name, BenchmarkStatus.DONE)
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert setup_transaction.benchmark.load(benchmark_name).unwrap().metrics[0].status == JobStatus.DONE
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "result", "exp"),
        [
            (
                "existing",
                "existing",
                MetricResultDomain.model_validate(MockConfig(something="xD").model_dump(), from_attributes=True),
                Success(None),
            ),
            (
                "non-existing",
                "existing",
                MetricResultDomain.model_validate(MockConfig(something="xD").model_dump(), from_attributes=True),
                Failure(DataNotExistError()),
            ),
            (
                "existing",
                "non-existing",
                MetricResultDomain.model_validate(MockConfig(something="xD").model_dump(), from_attributes=True),
                Failure(DataNotExistError()),
            ),
        ],
    )
    def test_result_storage(
        self,
        setup_transaction: DaoTransaction,
        benchmark_name: str,
        metric_name: str,
        result: MetricResultDomain,
        exp: Result[None, DataNotExistError],
    ) -> None:
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
