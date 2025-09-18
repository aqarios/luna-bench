from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import (
    BenchmarkStatus,
    ModelmetricConfigDomain,
    ModelmetricResultDomain,
)
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError

if TYPE_CHECKING:
    from luna_bench._internal.dao import StorageTransaction


class TestModelMetricDAO:
    _saved_modelmetric_domain: ModelmetricConfigDomain

    @pytest.fixture()
    @staticmethod
    def setup_transaction(empty_transaction: StorageTransaction) -> StorageTransaction:
        """Provide a transaction fixture with a default model for testing the ModelDAOs."""
        empty_transaction.benchmark.create(benchmark_name="existing")
        TestModelMetricDAO._saved_modelmetric_domain = empty_transaction.model_metric.add(
            benchmark_name="existing",
            modelmetric_name="existing",
            modelmetric_config=ModelmetricConfigDomain.ModelmetricConfig(something="xD"),
        ).unwrap()

        return empty_transaction

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "exp"),
        [
            (
                "existing",
                "non-existing",
                Success(
                    ModelmetricConfigDomain(
                        id=2,
                        name="non-existing",
                        status=BenchmarkStatus.CREATED,
                        result=None,
                        config_data=ModelmetricConfigDomain.ModelmetricConfig(something="xD"),
                    )
                ),
            ),
            ("existing", "existing", Failure(DataNotUniqueError())),
            ("non-existing", "non-existing", Failure(DataNotExistError())),
        ],
    )
    @staticmethod
    def test_add_modelmetric(
        setup_transaction: StorageTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.model_metric.add(
            benchmark_name, metric_name, ModelmetricConfigDomain.ModelmetricConfig(something="xD")
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert len(setup_transaction.benchmark.load(benchmark_name).unwrap().modelmetrics) == 2
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
    def test_load_modelmetric(
        setup_transaction: StorageTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.model_metric.load(benchmark_name, metric_name)
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == TestModelMetricDAO._saved_modelmetric_domain
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
    def test_remove_modelmetric(
        setup_transaction: StorageTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.model_metric.remove(benchmark_name, metric_name)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert len(setup_transaction.benchmark.load(benchmark_name).unwrap().modelmetrics) == 0
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
    def test_update_modelmetric(
        setup_transaction: StorageTransaction, benchmark_name: str, metric_name: str, exp: Result
    ) -> None:
        result = setup_transaction.model_metric.update(
            benchmark_name, metric_name, ModelmetricConfigDomain.ModelmetricConfig(something="xD2")
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert (
                setup_transaction.benchmark.load(benchmark_name).unwrap().modelmetrics[0].status
                == BenchmarkStatus.CREATED
            )
            assert (
                setup_transaction.benchmark.load(benchmark_name).unwrap().modelmetrics[0].config_data.something == "xD2"
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
        result = setup_transaction.model_metric.update_status(
            benchmark_name, metric_name, BenchmarkStatus.DONE
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
            assert (
                setup_transaction.benchmark.load(benchmark_name).unwrap().modelmetrics[0].status == BenchmarkStatus.DONE
            )
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("benchmark_name", "metric_name", "result", "exp"),
        [
            (
                "existing",
                "existing",
                ModelmetricResultDomain(v="result"),
                Success(None),
            ),
            ("non-existing", "existing", ModelmetricResultDomain(v="result"), Failure(DataNotExistError())),
            ("existing", "non-existing", ModelmetricResultDomain(v="result"), Failure(DataNotExistError())),
        ],
    )
    def test_result_storage(
        self,
        setup_transaction: StorageTransaction,
        benchmark_name: str,
        metric_name: str,
        result: ModelmetricResultDomain,
        exp: Result,
    ):
        set_result = setup_transaction.model_metric.set_result(benchmark_name, metric_name, result)
        assert type(set_result) is type(exp)
        if is_successful(exp):
            assert setup_transaction.model_metric.load(benchmark_name, metric_name).unwrap().result == result
        else:
            assert isinstance(set_result.failure(), type(exp.failure()))

        remove = setup_transaction.model_metric.remove_result(benchmark_name, metric_name)
        assert type(remove) is type(exp)
        if is_successful(exp):
            assert setup_transaction.model_metric.load(benchmark_name, metric_name).unwrap().result is None
        else:
            assert isinstance(remove.failure(), type(exp.failure()))
