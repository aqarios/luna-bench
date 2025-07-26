from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from luna_quantum import Model, Variable
from returns.result import Failure, Success

from luna_bench.errors.storage.data_not_exist import DataNotExistError

if TYPE_CHECKING:
    from luna_bench._internal.entities import ModelMetadataDomain, StorageTransaction


def _dummy_model(name: str) -> Model:
    model = Model(name)
    with model.environment:
        x = Variable("x")
        y = Variable("y")
    model.objective = x * y + x
    model.constraints += x >= 0
    model.constraints += y <= 5

    return model


class TestModelDAO:
    @pytest.fixture()
    @staticmethod
    def setup_transaction(empty_transaction: StorageTransaction) -> StorageTransaction:
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
        self, setup_transaction: StorageTransaction, model_hash: int, exp: Success[Model] | Failure[Exception]
    ) -> None:
        result = setup_transaction.model.get(model_hash=model_hash)

        assert type(result) is type(exp)

        if isinstance(exp, Success):
            TestModelDAO._check_model(exp.unwrap(), result.unwrap())

        elif isinstance(exp, Failure):
            TestModelDAO._check_exception(result.failure(), exp.failure())

    @pytest.mark.parametrize("exp", [([_dummy_model("M1"), _dummy_model("M2")])])
    def test_get_all_model(self, setup_transaction: StorageTransaction, exp: list[Model]) -> None:
        result: list[ModelMetadataDomain] = setup_transaction.model.get_all()

        result = sorted(result, key=lambda x: x.name)
        exp = sorted(exp, key=lambda x: x.name)

        for i in range(len(exp)):
            TestModelDAO._check_model(exp[i], result[i])
