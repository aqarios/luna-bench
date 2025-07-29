from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from returns.result import Failure, Result, Success

from luna_bench._internal.entities import ModelSetDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError

if TYPE_CHECKING:
    from luna_bench._internal.entities import StorageTransaction


class TestModelSetDAO:
    @pytest.fixture()
    @staticmethod
    def setup_transaction(empty_transaction: StorageTransaction) -> StorageTransaction:
        """Provide a transaction fixture with a default model for testing the ModelDAOs."""
        empty_transaction.modelset.create(name="Existing")
        return empty_transaction

    @pytest.mark.parametrize(
        ("name", "exp"),
        [
            ("Test", Success(ModelSetDomain(id=2, name="Test", models=[]))),
            ("Existing", Failure(DataNotUniqueError())),
        ],
    )
    def test_create_modelset(
        self, setup_transaction: StorageTransaction, name: str, exp: Result[[ModelSetDomain], Failure[Exception]]
    ) -> None:
        result = setup_transaction.modelset.create(name=name)

        assert type(result) is type(exp)

        if isinstance(exp, Success):
            assert result.unwrap() == exp.unwrap()

        elif isinstance(exp, Failure):
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("modelset_id", "exp"),
        [
            (1, Success(ModelSetDomain(id=1, name="Existing", models=[]))),
            (2, Failure(DataNotExistError())),
        ],
    )
    def test_load_modelset(
        self, setup_transaction: StorageTransaction, modelset_id: int, exp: Result[[ModelSetDomain], Failure[Exception]]
    ) -> None:
        result = setup_transaction.modelset.load(modelset_id=modelset_id)

        assert type(result) is type(exp)

        if isinstance(exp, Success):
            assert result.unwrap() == exp.unwrap()

        elif isinstance(exp, Failure):
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("modelset_id", "exp"),
        [
            (1, Success(None)),
            (2, Failure(DataNotExistError())),
        ],
    )
    def test_delete_modelset(
        self, setup_transaction: StorageTransaction, modelset_id: int, exp: Result[[ModelSetDomain], Failure[Exception]]
    ) -> None:
        result = setup_transaction.modelset.delete(modelset_id=modelset_id)

        assert type(result) is type(exp)

        if isinstance(exp, Success):
            assert result.unwrap() == exp.unwrap()

            get_result = setup_transaction.modelset.load(modelset_id=modelset_id)
            assert isinstance(get_result.failure(), DataNotExistError)

        elif isinstance(exp, Failure):
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("modelset_id", "exp"),
        [
            (1, Success(None)),
        ],
    )
    def test_add_model(
        self, setup_transaction: StorageTransaction, modelset_id: int, exp: Result[[ModelSetDomain], Failure[Exception]]
    ) -> None:
        raise NotImplementedError

    @pytest.mark.parametrize(
        ("modelset_id", "exp"),
        [
            (1, Success(None)),
        ],
    )
    def test_remove_model(
        self, setup_transaction: StorageTransaction, modelset_id: int, exp: Result[[ModelSetDomain], Failure[Exception]]
    ) -> None:
        raise NotImplementedError

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
        self, setup_transaction: StorageTransaction, exp: Result[list[ModelSetDomain], Failure[Exception]]
    ) -> None:
        result = setup_transaction.modelset.load_all()

        assert type(result) is type(exp)
        assert result.unwrap() == exp.unwrap()

    @pytest.mark.parametrize(
        ("modelset_id", "exp"),
        [
            (
                1,
                Success(
                    [
                        ModelSetDomain(id=1, name="Existing", models=[]),
                    ]
                ),
            ),
        ],
    )
    def test_load_all_models(
        self,
        setup_transaction: StorageTransaction,
        modelset_id: int,
        exp: Result[list[ModelSetDomain], Failure[Exception]],
    ) -> None:
        raise NotImplementedError
