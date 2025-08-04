from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from luna_quantum import Model, Variable
from returns.result import Failure, Result, Success

from luna_bench._internal.entities import ModelMetadataDomain, ModelSetDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError

if TYPE_CHECKING:
    from luna_bench._internal.entities import StorageTransaction
    from luna_bench.errors.unknown_error import UnknownLunaBenchError


def _dummy_model(name: str) -> Model:
    model = Model(name)
    with model.environment:
        x = Variable("x")
        y = Variable("y")
    model.objective = x * y + x
    model.constraints += x >= 0
    model.constraints += y <= 5

    return model


def _stored_dummy_model(transaction: StorageTransaction, modelset_name: str, model_name: str) -> ModelMetadataDomain:
    model = _dummy_model(model_name)
    model_metadata = transaction.model.get_or_create(
        model_name=model.name, model_hash=model.__hash__(), binary=model.encode()
    ).unwrap()
    transaction.modelset.add_model(modelset_name=modelset_name, model_id=model_metadata.id)
    return model_metadata


class TestModelSetDAO:
    @pytest.fixture()
    @staticmethod
    def setup_transaction(empty_transaction: StorageTransaction) -> StorageTransaction:
        """Provide a transaction fixture with a default model for testing the ModelDAOs."""
        empty_transaction.modelset.create(modelset_name="Existing")
        return empty_transaction

    @pytest.mark.parametrize(
        ("name", "exp"),
        [
            ("Test", Success(ModelSetDomain(id=2, name="Test", models=[]))),
            ("Existing", Failure(DataNotUniqueError())),
        ],
    )
    def test_create_modelset(
        self,
        setup_transaction: StorageTransaction,
        name: str,
        exp: Result[ModelSetDomain, DataNotUniqueError | UnknownLunaBenchError],
    ) -> None:
        result = setup_transaction.modelset.create(modelset_name=name)

        assert type(result) is type(exp)

        if isinstance(exp, Success):
            assert result.unwrap() == exp.unwrap()

        elif isinstance(exp, Failure):
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("modelset_name", "exp"),
        [
            ("Existing", Success(ModelSetDomain(id=1, name="Existing", models=[]))),
            ("existing", Success(ModelSetDomain(id=1, name="Existing", models=[]))),
            ("exiSTing", Success(ModelSetDomain(id=1, name="Existing", models=[]))),
            (2, Failure(DataNotExistError())),
        ],
    )
    def test_load_modelset(
        self,
        setup_transaction: StorageTransaction,
        modelset_name: str,
        exp: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        result = setup_transaction.modelset.load(modelset_name=modelset_name)

        assert type(result) is type(exp)

        if isinstance(exp, Success):
            assert result.unwrap() == exp.unwrap()

        elif isinstance(exp, Failure):
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("modelset_name", "exp"),
        [
            ("Existing", Success(None)),
            ("NotExisting", Failure(DataNotExistError())),
        ],
    )
    def test_delete_modelset(
        self,
        setup_transaction: StorageTransaction,
        modelset_name: str,
        exp: Result[None, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        result = setup_transaction.modelset.delete(modelset_name=modelset_name)

        assert type(result) is type(exp)

        if isinstance(exp, Success):
            assert result.unwrap() == exp.unwrap()

            get_result = setup_transaction.modelset.load(modelset_name=modelset_name)
            assert isinstance(get_result.failure(), DataNotExistError)

        elif isinstance(exp, Failure):
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("modelset_name", "models", "exp"),
        [
            ("Existing", [_dummy_model("Test")], Success(ModelSetDomain(id=1, name="Existing", models=[]))),
            (
                "Existing",
                [_dummy_model("Test"), _dummy_model("Test2")],
                Success(ModelSetDomain(id=1, name="Existing", models=[])),
            ),
            ("Existing", [], Failure(DataNotExistError())),
        ],
    )
    def test_add_model(
        self,
        setup_transaction: StorageTransaction,
        modelset_name: str,
        models: list[Model],
        exp: Result[ModelSetDomain, Exception],
    ) -> None:
        result: Result[ModelSetDomain, Exception] | None = None

        for model in models:
            model_stored = setup_transaction.model.get_or_create(
                model_name=model.name, model_hash=model.__hash__(), binary=model.encode()
            ).unwrap()
            result = setup_transaction.modelset.add_model(modelset_name=modelset_name, model_id=model_stored.id)

        if result is None:
            result = setup_transaction.modelset.add_model(modelset_name=modelset_name, model_id=10)

        loaded_modelset = setup_transaction.modelset.load(modelset_name=modelset_name)

        assert type(result) is type(exp)

        if isinstance(exp, Success):
            assert result.unwrap().id == exp.unwrap().id
            assert len(result.unwrap().models) == len(models)
            assert result.unwrap().models == loaded_modelset.unwrap().models

        elif isinstance(exp, Failure):
            assert isinstance(result.failure(), type(exp.failure()))
            assert len(loaded_modelset.unwrap().models) == 0

    @pytest.mark.parametrize(
        ("modelset_name", "model_id", "exp"),
        [
            ("Existing", 1, Success(ModelSetDomain(id=1, name="Existing", models=[]))),
            ("Existing", 2, Failure(DataNotExistError())),
        ],
    )
    def test_remove_model(
        self,
        setup_transaction: StorageTransaction,
        modelset_name: str,
        model_id: int,
        exp: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        _stored_dummy_model(setup_transaction, modelset_name, "Test")

        result = setup_transaction.modelset.remove_model(modelset_name=modelset_name, model_id=model_id)
        loaded_modelset = setup_transaction.modelset.load(modelset_name=modelset_name)
        assert type(result) is type(exp)

        if isinstance(exp, Success):
            assert loaded_modelset.unwrap() == exp.unwrap()
            assert result.unwrap() == exp.unwrap()
            assert result.unwrap().models == []
            assert result.unwrap().name == modelset_name

        elif isinstance(exp, Failure):
            assert isinstance(result.failure(), type(exp.failure()))
            assert len(loaded_modelset.unwrap().models) == 1

    @pytest.mark.parametrize(
        ("exp"),
        [
            (
                Success(
                    [
                        ModelSetDomain(id=1, name="Existing", models=[]),
                    ]
                )
            ),
        ],
    )
    def test_load_all(
        self, setup_transaction: StorageTransaction, exp: Result[list[ModelSetDomain], UnknownLunaBenchError]
    ) -> None:
        result = setup_transaction.modelset.load_all()

        assert type(result) is type(exp)
        assert result.unwrap() == exp.unwrap()

    @pytest.mark.parametrize(
        ("modelset_name", "exp"),
        [
            ("Existing", Success([])),
            ("NotExisting", Failure(DataNotExistError())),
        ],
    )
    def test_load_all_models(
        self,
        setup_transaction: StorageTransaction,
        modelset_name: str,
        exp: Result[list[ModelMetadataDomain], DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        _stored_dummy_model(setup_transaction, modelset_name, "Test1")
        _stored_dummy_model(setup_transaction, modelset_name, "Test2")

        result = setup_transaction.modelset.load_all_models(modelset_name=modelset_name)

        assert type(result) is type(exp)

        if isinstance(exp, Success):
            assert len(result.unwrap()) == 2
            assert result.unwrap()[0].name == "Test1"
            assert result.unwrap()[1].name == "Test2"

        elif isinstance(exp, Failure):
            assert isinstance(result.failure(), type(exp.failure()))
