from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from tests.unit.fixtures.mock_model import _dummy_model

if TYPE_CHECKING:
    from luna_quantum import Model

    from luna_bench._internal.dao import DaoTransaction
    from luna_bench._internal.domain_models import ModelMetadataDomain
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


class TestModelDAO:
    @pytest.fixture()
    @staticmethod
    def setup_transaction(empty_transaction: DaoTransaction) -> DaoTransaction:
        """Provide a transaction fixture with a default model for testing the ModelDAOs."""
        model: Model = _dummy_model("M1")
        model2: Model = _dummy_model("M2")
        empty_transaction.model.get_or_create(model_name=model.name, model_hash=model.__hash__(), binary=model.encode())
        empty_transaction.model.get_or_create(
            model_name=model2.name, model_hash=model2.__hash__(), binary=model2.encode()
        )

        return empty_transaction

    @staticmethod
    def _check_model(model: Model, model_metadata: ModelMetadataDomain) -> None:
        assert isinstance(model_metadata.id, int)
        assert model_metadata.name == model.name
        assert model_metadata.hash == model.__hash__()

    @staticmethod
    def _check_exception(exception: Exception, expectation: Exception) -> None:
        assert isinstance(exception, type(expectation))

    @pytest.mark.parametrize(
        ("model_hash", "exp"),
        [
            (_dummy_model("M1").__hash__(), Success(_dummy_model("M1"))),
            (_dummy_model("M2").__hash__(), Success(_dummy_model("M2"))),
            (1, Failure(DataNotExistError())),
        ],
    )
    def test_get_model(
        self,
        setup_transaction: DaoTransaction,
        model_hash: int,
        exp: Result[Model, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        result = setup_transaction.model.get(model_hash=model_hash)

        assert type(result) is type(exp)

        if isinstance(exp, Success):
            TestModelDAO._check_model(exp.unwrap(), result.unwrap())

        elif isinstance(exp, Failure):
            TestModelDAO._check_exception(result.failure(), exp.failure())

    @pytest.mark.parametrize("exp", [([_dummy_model("M1"), _dummy_model("M2")])])
    def test_get_all_model(self, setup_transaction: DaoTransaction, exp: list[Model]) -> None:
        result: list[ModelMetadataDomain] = setup_transaction.model.get_all()

        result = sorted(result, key=lambda x: x.name)
        exp = sorted(exp, key=lambda x: x.name)

        for i in range(len(exp)):
            TestModelDAO._check_model(exp[i], result[i])

    @pytest.mark.parametrize(
        ("model", "exp"),
        [
            (_dummy_model("Test"), Success(_dummy_model("Test"))),
            (_dummy_model("M1"), Success(_dummy_model("M1"))),
        ],
    )
    def test_get_or_create_model(
        self, setup_transaction: DaoTransaction, model: Model, exp: Result[Model, Exception]
    ) -> None:
        model_stored = setup_transaction.model.get(model_hash=model.__hash__())
        result = setup_transaction.model.get_or_create(
            model_name=model.name, model_hash=model.__hash__(), binary=model.encode()
        )

        if isinstance(exp, Success):
            new_model = result.unwrap()
            TestModelDAO._check_model(exp.unwrap(), new_model)
            assert new_model.id is not None

            if is_successful(model_stored):
                assert new_model.id == model_stored.unwrap().id
            else:
                # Model was before not stored, so let's check if the actual model was stored an not only metadata
                assert setup_transaction.model.load(new_model.id).unwrap() == model.encode()
        elif isinstance(exp, Failure):
            TestModelDAO._check_exception(result.failure(), exp.failure())

    def test_fetch_model(self, setup_transaction: DaoTransaction) -> None:
        model_exists = _dummy_model("M1")
        model_stored = setup_transaction.model.get(model_hash=model_exists.__hash__())

        fetch_success = setup_transaction.model.load(model_id=model_stored.unwrap().id)

        assert fetch_success.unwrap() == model_exists.encode()

        fetch_failed = setup_transaction.model.load(model_id=-1)

        TestModelDAO._check_exception(fetch_failed.failure(), DataNotExistError())
