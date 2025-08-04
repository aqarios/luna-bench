from contextlib import nullcontext
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
from luna_quantum import Model
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.entities import ModelMetadataDomain, ModelSetDomain
from luna_bench._internal.usecases.usecase_container import UsecaseContainer
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from tests.unit.fixtures.mock_usecase import _dummy_model

if TYPE_CHECKING:
    from luna_bench._internal.usecases import ModelSetAddUc, ModelSetCreateUc, ModelSetDeleteUc
    from luna_bench._internal.usecases.modelset import ModelSetRemoveUc
    from luna_bench._internal.usecases.modelset.protocols import ModelSetLoadAllUc, ModelSetLoadUc


class TestModelsetUc:
    @pytest.mark.parametrize(
        ("modelset_name", "exp"),
        [
            ("MS1", Failure(DataNotUniqueError())),
            ("MS2", Success(ModelSetDomain(id=2, name="MS2", models=[]))),
        ],
    )
    def test_create(
        self,
        usecase: UsecaseContainer,
        modelset_name: str,
        exp: Result[ModelSetDomain, DataNotUniqueError | UnknownLunaBenchError],
    ) -> None:
        uc: ModelSetCreateUc = usecase.modelset_create_uc()
        result: Result[ModelSetDomain, DataNotUniqueError | UnknownLunaBenchError] = uc(
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
            ("MS1", _dummy_model("M3"), 3, Success(None)),
            ("MS1", _dummy_model("M1"), 2, Success(None)),
            ("MS3", _dummy_model("M3"), 2, Failure(DataNotExistError())),
        ],
    )
    def test_add_model(
        self,
        usecase: UsecaseContainer,
        modelset_name: str,
        model: Model,
        models_after_add: int,
        exp: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        uc: ModelSetAddUc = usecase.modelset_add_uc()
        result: Result[ModelSetDomain, DataNotExistError | DataNotUniqueError | UnknownLunaBenchError] = uc(
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
        uc: ModelSetAddUc = usecase.modelset_add_uc()

        translation_mock = Mock()
        translation_mock.model.get_or_create = Mock(
            return_value=Failure(UnknownLunaBenchError(exception=RuntimeError()))
        )
        uc._transaction = nullcontext(translation_mock)  # type: ignore[attr-defined] # Overwrite the var so we can return a failure here

        result: Result[ModelSetDomain, DataNotExistError | DataNotUniqueError | UnknownLunaBenchError] = uc(
            modelset_name="A", model=_dummy_model("M3")
        )
        assert isinstance(result.failure(), UnknownLunaBenchError)

    @pytest.mark.parametrize(
        ("modelset_name", "exp"),
        [
            ("MS1", Failure(DataNotUniqueError())),
            ("MS2", Success(ModelSetDomain(id=2, name="MS2", models=[]))),
        ],
    )
    def test_model_create(
        self,
        usecase: UsecaseContainer,
        modelset_name: str,
        exp: Result[ModelSetDomain, DataNotUniqueError | UnknownLunaBenchError],
    ) -> None:
        uc: ModelSetCreateUc = usecase.modelset_create_uc()
        result: Result[ModelSetDomain, DataNotUniqueError | UnknownLunaBenchError] = uc(
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
                "MS1",
                _dummy_model("M2"),
                Success(
                    ModelSetDomain(
                        id=1,
                        name="MS1",
                        models=[ModelMetadataDomain(id=1, name="M1", hash=_dummy_model("M1").__hash__())],
                    )
                ),
            ),
            ("MS1", _dummy_model("M3"), Failure(DataNotExistError())),
            ("MS3", _dummy_model("M1"), Failure(DataNotExistError())),
        ],
    )
    def test_remove_model(
        self,
        usecase: UsecaseContainer,
        modelset_name: str,
        model: Model,
        exp: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        uc: ModelSetRemoveUc = usecase.modelset_remove_uc()
        result: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError] = uc(
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
            ("MS1", Success(None)),
            ("MS2", Failure(DataNotExistError())),
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
            ("MS1", Success(ModelSetDomain(id=1, name="MS1", models=[]))),
            ("MS2", Failure(DataNotExistError())),
        ],
    )
    def test_modelset_load(
        self,
        usecase: UsecaseContainer,
        modelset_name: str,
        exp: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        uc: ModelSetLoadUc = usecase.modelset_load_uc()
        result: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError] = uc(modelset_name=modelset_name)
        assert type(result) is type(exp)

        if is_successful(exp):
            ms1 = result.unwrap()
            ex_modelset = exp.unwrap()
            assert ms1.name == ex_modelset.name
            assert ms1.id == ex_modelset.id
            assert len(ms1.models) == 2

        else:
            assert isinstance(result.failure(), type(exp.failure()))

    def test_modelset_load_all(
        self,
        usecase: UsecaseContainer,
    ) -> None:
        uc: ModelSetLoadAllUc = usecase.modelset_load_all_uc()
        result: Result[list[ModelSetDomain], UnknownLunaBenchError] = uc()

        assert is_successful(result)

        assert len(result.unwrap()) == 1
