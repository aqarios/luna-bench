from typing import TYPE_CHECKING

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
        ("modelset_id", "model", "models_after_add", "exp"),
        [
            (1, _dummy_model("M3"), 3, Success(None)),
            (1, _dummy_model("M1"), 2, Success(None)),
            (3, _dummy_model("M3"), 2, Failure(DataNotExistError())),
        ],
    )
    def test_add_model(
        self,
        usecase: UsecaseContainer,
        modelset_id: int,
        model: Model,
        models_after_add: int,
        exp: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        uc: ModelSetAddUc = usecase.modelset_add_uc()
        result: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError] = uc(
            modelset_id=modelset_id, model=model
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            modelset = result.unwrap()
            assert len(modelset.models) == models_after_add
        else:
            assert isinstance(result.failure(), type(exp.failure()))

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
        ("modelset_id", "model", "exp"),
        [
            (
                1,
                _dummy_model("M2"),
                Success(
                    ModelSetDomain(
                        id=1,
                        name="MS1",
                        models=[ModelMetadataDomain(id=1, name="M1", hash=_dummy_model("M1").__hash__())],
                    )
                ),
            ),
            (1, _dummy_model("M3"), Failure(DataNotExistError())),
            (3, _dummy_model("M1"), Failure(DataNotExistError())),
        ],
    )
    def test_remove_model(
        self,
        usecase: UsecaseContainer,
        modelset_id: int,
        model: Model,
        exp: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        uc: ModelSetRemoveUc = usecase.modelset_remove_uc()
        result: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError] = uc(
            modelset_id=modelset_id, model=model
        )
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("modelset_id", "exp"),
        [
            (1, Success(None)),
            (2, Failure(DataNotExistError())),
        ],
    )
    def test_delete(
        self,
        usecase: UsecaseContainer,
        modelset_id: int,
        exp: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError],
    ) -> None:
        uc: ModelSetDeleteUc = usecase.modelset_delete_uc()
        result: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError] = uc(modelset_id=modelset_id)
        assert type(result) is type(exp)

        if is_successful(exp):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))
