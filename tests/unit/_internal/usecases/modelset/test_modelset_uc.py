from contextlib import nullcontext
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, Mock

import pytest
from luna_quantum import Model
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoTransaction, ModelSetDao
from luna_bench._internal.usecases.modelset import ModelSetLoadAllUcImpl
from luna_bench._internal.usecases.usecase_container import UsecaseContainer
from luna_bench._internal.user_models.model_set_usermodel import ModelSetUserModel
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from tests.utils.luna_model import simple_model

if TYPE_CHECKING:
    from luna_bench._internal.usecases import ModelAddUc, ModelSetCreateUc, ModelSetDeleteUc
    from luna_bench._internal.usecases.modelset.protocols import ModelRemoveUc, ModelSetLoadAllUc, ModelSetLoadUc


class TestModelsetUc:
    @pytest.mark.parametrize(
        ("modelset_name", "exp"),
        [
            ("existing", Failure(DataNotUniqueError())),
            ("non-existing", Success(ModelSetUserModel(id=2, name="non-existing", models=[]))),
        ],
    )
    def test_create(
        self,
        usecase: UsecaseContainer,
        modelset_name: str,
        exp: Result[ModelSetUserModel, DataNotUniqueError | UnknownLunaBenchError],
    ) -> None:
        uc: ModelSetCreateUc = usecase.modelset_create_uc()
        result: Result[ModelSetUserModel, DataNotUniqueError | UnknownLunaBenchError] = uc(
            modelset_name=modelset_name,
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("modelset_name", "model", "models_after_add", "exp"),
        [
            ("existing", simple_model("non-existing"), 2, Success(None)),
            ("existing", simple_model("existing"), 1, Success(None)),
            ("non-existing", simple_model("non-existing"), 1, Failure(DataNotExistError())),
        ],
    )
    def test_add_model(
        self,
        usecase: UsecaseContainer,
        modelset_name: str,
        model: Model,
        models_after_add: int,
        exp: Result[ModelSetUserModel, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        uc: ModelAddUc = usecase.model_add_uc()
        result: Result[ModelSetUserModel, DataNotExistError | DataNotUniqueError | UnknownLunaBenchError] = uc(
            modelset_name=modelset_name, model=model
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            modelset = result.unwrap()
            assert len(modelset.models) == models_after_add
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    def test_add_model_storage_issue(
        self,
        usecase: UsecaseContainer,
    ) -> None:
        uc: ModelAddUc = usecase.model_add_uc()

        transaction_mock = Mock()
        transaction_mock.model.get_or_create = Mock(
            return_value=Failure(UnknownLunaBenchError(exception=RuntimeError()))
        )
        uc._transaction = nullcontext(transaction_mock)  # type: ignore[attr-defined] # Overwrite the var so we can return a failure here

        result: Result[ModelSetUserModel, DataNotExistError | DataNotUniqueError | UnknownLunaBenchError] = uc(
            modelset_name="A", model=simple_model("M3")
        )
        assert isinstance(result.failure(), UnknownLunaBenchError)

    @pytest.mark.parametrize(
        ("modelset_name", "exp"),
        [
            ("existing", Failure(DataNotUniqueError())),
            ("non-existing", Success(ModelSetUserModel(id=2, name="non-existing", models=[]))),
        ],
    )
    def test_model_create(
        self,
        usecase: UsecaseContainer,
        modelset_name: str,
        exp: Result[ModelSetUserModel, DataNotUniqueError | UnknownLunaBenchError],
    ) -> None:
        uc: ModelSetCreateUc = usecase.modelset_create_uc()
        result: Result[ModelSetUserModel, DataNotUniqueError | UnknownLunaBenchError] = uc(
            modelset_name=modelset_name,
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("modelset_name", "model", "exp"),
        [
            (
                "existing",
                simple_model("existing"),
                Success(
                    ModelSetUserModel(
                        id=1,
                        name="existing",
                        models=[],
                    )
                ),
            ),
            ("existing", simple_model("non-existing"), Failure(DataNotExistError())),
            ("non-existing", simple_model("existing"), Failure(DataNotExistError())),
        ],
    )
    def test_remove_model(
        self,
        usecase: UsecaseContainer,
        modelset_name: str,
        model: Model,
        exp: Result[ModelSetUserModel, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        uc: ModelRemoveUc = usecase.model_remove_uc()
        result: Result[ModelSetUserModel, DataNotExistError | UnknownLunaBenchError] = uc(
            modelset_name=modelset_name, model=model
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("modelset_name", "exp"),
        [
            ("existing", Success(None)),
            ("non-existing", Failure(DataNotExistError())),
        ],
    )
    def test_delete(
        self,
        usecase: UsecaseContainer,
        modelset_name: str,
        exp: Result[None, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        uc: ModelSetDeleteUc = usecase.modelset_delete_uc()
        result: Result[None, DataNotExistError | UnknownLunaBenchError] = uc(modelset_name=modelset_name)
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("modelset_name", "exp"),
        [
            ("existing", Success(ModelSetUserModel(id=1, name="existing", models=[]))),
            ("non-existing", Failure(DataNotExistError())),
        ],
    )
    def test_modelset_load(
        self,
        usecase: UsecaseContainer,
        modelset_name: str,
        exp: Result[ModelSetUserModel, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        uc: ModelSetLoadUc = usecase.modelset_load_uc()
        result: Result[ModelSetUserModel, DataNotExistError | UnknownLunaBenchError] = uc(modelset_name=modelset_name)
        assert type(result) is type(exp)

        if is_successful(exp):
            ms1 = result.unwrap()
            ex_modelset = exp.unwrap()
            assert ms1.name == ex_modelset.name
            assert ms1.id == ex_modelset.id
            assert len(ms1.models) == 1

        else:
            assert isinstance(result.failure(), type(exp.failure()))

    def test_modelset_load_all(
        self,
        usecase: UsecaseContainer,
    ) -> None:
        uc: ModelSetLoadAllUc = usecase.modelset_load_all_uc()
        result: Result[list[ModelSetUserModel], UnknownLunaBenchError] = uc()

        assert is_successful(result)

        assert len(result.unwrap()) == 1

    def test_modelset_load_all_error(self) -> None:
        mock_dao = Mock(spec=ModelSetDao)
        mock_dao.load_all.return_value = Failure(UnknownLunaBenchError(exception=RuntimeError()))

        mock_transaction = MagicMock(spec=DaoTransaction)
        mock_transaction.__enter__.return_value = mock_transaction
        mock_transaction.modelset = mock_dao  # Works on Mock objects!

        r = ModelSetLoadAllUcImpl(transaction=mock_transaction)()
        assert not is_successful(r)
        assert isinstance(r.failure(), UnknownLunaBenchError)
