"""Failure branches of use cases that are only reachable when a DAO call fails.

These paths need a transaction that returns ``Failure`` on demand, which the in-memory
database used elsewhere never does, so they are driven with mocked transactions.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Success

from luna_bench._internal.usecases.benchmark.benchmark_load_all import BenchmarkLoadAllUcImpl
from luna_bench._internal.usecases.modelset.model.model_add import ModelAddUcImpl
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.model_name_already_used_error import ModelNameAlreadyUsedError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from tests.utils.luna_model import simple_model


def mock_transaction() -> MagicMock:
    """Build a transaction whose ``with`` block yields a fully mocked DAO set."""
    transaction = MagicMock()
    transaction.__enter__.return_value = transaction.dao = MagicMock()
    transaction.__exit__.return_value = False
    return transaction


@pytest.fixture()
def transaction() -> MagicMock:
    return mock_transaction()


class TestBenchmarkLoadAll:
    """Both the DAO read and the per-benchmark mapping can fail."""

    def test_a_failing_dao_read_is_propagated(self, transaction: MagicMock) -> None:
        failure = UnknownLunaBenchError(RuntimeError("db down"))
        transaction.dao.benchmark.load_all.return_value = Failure(failure)

        uc = BenchmarkLoadAllUcImpl(transaction=transaction, benchmark_mapper=MagicMock())
        result = uc()

        assert not is_successful(result)
        assert result.failure() is failure

    def test_a_failing_mapping_is_propagated(self, transaction: MagicMock) -> None:
        failure = UnknownLunaBenchError(RuntimeError("bad row"))
        transaction.dao.benchmark.load_all.return_value = Success([MagicMock()])
        mapper = MagicMock()
        mapper.to_user_model.return_value = Failure(failure)

        uc = BenchmarkLoadAllUcImpl(transaction=transaction, benchmark_mapper=mapper)
        result = uc()

        assert not is_successful(result)
        assert result.failure() is failure

    def test_every_benchmark_is_mapped_on_success(self, transaction: MagicMock) -> None:
        first, second = MagicMock(), MagicMock()
        transaction.dao.benchmark.load_all.return_value = Success([MagicMock(), MagicMock()])
        mapper = MagicMock()
        mapper.to_user_model.side_effect = [Success(first), Success(second)]

        uc = BenchmarkLoadAllUcImpl(transaction=transaction, benchmark_mapper=mapper)

        assert uc().unwrap() == [first, second]
        assert mapper.to_user_model.call_count == 2


class TestModelAdd:
    """A name clash is reported as `ModelNameAlreadyUsedError`, other errors pass through."""

    def test_a_duplicate_name_is_translated(self, transaction: MagicMock) -> None:
        transaction.dao.model.get_or_create.return_value = Failure(DataNotUniqueError())

        uc = ModelAddUcImpl(transaction=transaction)
        result = uc(modelset_name="ms", model=simple_model("clashing"))

        error = result.failure()
        assert isinstance(error, ModelNameAlreadyUsedError)
        assert "clashing" in str(error)

    def test_any_other_error_is_passed_through(self, transaction: MagicMock) -> None:
        failure = UnknownLunaBenchError(RuntimeError("db down"))
        transaction.dao.model.get_or_create.return_value = Failure(failure)

        uc = ModelAddUcImpl(transaction=transaction)

        assert uc(modelset_name="ms", model=simple_model("m")).failure() is failure

    def test_a_failing_modelset_add_is_passed_through(self, transaction: MagicMock) -> None:
        failure = DataNotExistError()
        transaction.dao.model.get_or_create.return_value = Success(MagicMock())
        transaction.dao.modelset.add_model.return_value = Failure(failure)

        uc = ModelAddUcImpl(transaction=transaction)

        assert uc(modelset_name="ms", model=simple_model("m")).failure() is failure
