from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import MetricConfigDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError

if TYPE_CHECKING:
    from luna_bench._internal.dao import StorageTransaction


class TestMetricDAO:
    @pytest.fixture()
    @staticmethod
    def setup_transaction(empty_transaction: StorageTransaction) -> StorageTransaction:
        """Provide a transaction fixture with a default model for testing the ModelDAOs."""
        empty_transaction.benchmark.create(benchmark_name="existing")
        empty_transaction.metric.add_metric(
            benchmark_name="existing",
            metric_name="existing",
            metric_config=MetricConfigDomain.MetricConfig(something="xD"),
        )

        return empty_transaction

    @pytest.mark.parametrize(
        ("metric_name", "exp"),
        [
            (
                "non-existing",
                Success(None),
            ),
            ("existing", Failure(DataNotUniqueError())),
        ],
    )
    @staticmethod
    def test_add_metric(setup_transaction: StorageTransaction, metric_name: str, exp: Result) -> None:
        result = setup_transaction.metric.add_metric(
            "existing", metric_name, MetricConfigDomain.MetricConfig(something="xD")
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert len(setup_transaction.benchmark.load("existing").unwrap().metrics) == 1
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
        setup_transaction: StorageTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.metric.remove_metric("existing", "existing")

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert len(setup_transaction.benchmark.load("existing").unwrap().plots) == 0
        else:
            assert isinstance(result.failure(), type(exp.failure()))
