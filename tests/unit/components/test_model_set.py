from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext
from unittest.mock import Mock

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

import luna_bench
from luna_bench._internal.domain_models import ModelMetadataDomain, ModelSetDomain
from luna_bench._internal.usecases.modelset.protocols import (
    ModelAddUc,
    ModelLoadAllUc,
    ModelRemoveUc,
    ModelSetCreateUc,
    ModelSetDeleteUc,
    ModelSetLoadAllUc,
    ModelSetLoadUc,
)
from luna_bench.components import ModelMetadata, ModelSet
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from tests.utils.luna_model import simple_model


class TestModelData:
    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            (
                Success(ModelSetDomain(id=1, name="Test", models=[])),
                nullcontext(ModelSet(id=1, name="Test", models=[])),
            ),
        ],
    )
    def test_create(
        self,
        return_value: Result[ModelSetDomain, Exception],
        exp: AbstractContextManager[ModelSet],
    ) -> None:
        mock: Mock = Mock(spec=ModelSetCreateUc)
        mock.return_value = return_value
        with exp as e, luna_bench._usecase_container.modelset_create_uc.override(mock):
            r = ModelSet.create(modelset_name="Test")
            mock.assert_called_with(modelset_name="Test")

            assert e == r

    @pytest.mark.parametrize(
        ("modelset_name", "load_return_value", "exp"),
        [
            (
                "Test",
                Success(ModelSetDomain(id=1, name="Test", models=[])),
                nullcontext(ModelSet(id=1, name="Test", models=[])),
            ),
            (
                "Existing",
                Success(ModelSetDomain(id=2, name="Existing", models=[])),
                nullcontext(ModelSet(id=2, name="Existing", models=[])),
            ),
        ],
    )
    def test_create_when_duplicate(
        self,
        modelset_name: str,
        load_return_value: Result[ModelSetDomain, UnknownLunaBenchError],
        exp: AbstractContextManager[ModelSet],
    ) -> None:
        create_mock: Mock = Mock(spec=ModelSetCreateUc)
        create_mock.return_value = Failure(DataNotUniqueError())

        load_mock: Mock = Mock(spec=ModelSetLoadUc)
        load_mock.return_value = load_return_value

        with (
            exp as e,
            luna_bench._usecase_container.modelset_create_uc.override(create_mock),
            luna_bench._usecase_container.modelset_load_uc.override(load_mock),
        ):
            r = ModelSet.create(modelset_name=modelset_name)
            create_mock.assert_called_with(modelset_name=modelset_name)
            assert e == r

    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            ([ModelMetadataDomain(id=1, name="A", hash=1)], [ModelMetadata(id=1, name="A", hash=1)]),
            ([], []),
        ],
    )
    def test_load_all_models(self, return_value: list[ModelMetadataDomain], exp: list[ModelMetadata]) -> None:
        mock: Mock = Mock(spec=ModelLoadAllUc)
        mock.return_value = return_value
        with luna_bench._usecase_container.model_load_all_uc.override(mock):
            r = ModelSet.load_all_models()
            mock.assert_called_with()

        assert exp == r

    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            (
                Success(ModelSetDomain(id=1, name="B", models=[ModelMetadataDomain(id=1, name="A", hash=1)])),
                nullcontext(ModelSet(id=1, name="B", models=[ModelMetadata(id=1, name="A", hash=1)])),
            ),
            (Failure(DataNotExistError()), pytest.raises(RuntimeError)),
        ],
    )
    def test_add_model(
        self, return_value: Result[ModelSetDomain, Exception], exp: AbstractContextManager[ModelSet | RuntimeError]
    ) -> None:
        mock: Mock = Mock(spec=ModelAddUc)
        mock.return_value = return_value
        modelset = ModelSet(id=1, name="B", models=[])

        with exp as e, luna_bench._usecase_container.model_add_uc.override(mock):
            model = simple_model("A")
            modelset.add(model=model)
            mock.assert_called_with(modelset_name=return_value.unwrap().name, model=model)
            assert e == modelset

    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            (Success(ModelSetDomain(id=1, name="a", models=[])), nullcontext(ModelSet(id=1, name="a", models=[]))),
            (Failure(UnknownLunaBenchError(exception=RuntimeError())), pytest.raises(RuntimeError)),
        ],
    )
    def test_load(
        self,
        return_value: Result[ModelSetDomain, UnknownLunaBenchError],
        exp: AbstractContextManager[ModelSet | RuntimeError],
    ) -> None:
        mock: Mock = Mock(spec=ModelSetLoadUc)
        mock.return_value = return_value

        name: str = return_value.unwrap().name if is_successful(return_value) else "a"
        with exp as e, luna_bench._usecase_container.modelset_load_uc.override(mock):
            m = ModelSet.load(name=name)
            assert m == e

    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            (Success([]), nullcontext([])),
            (Success([ModelSetDomain(id=1, name="a", models=[])]), nullcontext([ModelSet(id=1, name="a", models=[])])),
            (Failure(UnknownLunaBenchError(exception=RuntimeError())), pytest.raises(RuntimeError)),
        ],
    )
    def test_load_all(
        self,
        return_value: Result[list[ModelSetDomain], UnknownLunaBenchError],
        exp: AbstractContextManager[list[ModelSet] | RuntimeError],
    ) -> None:
        mock: Mock = Mock(spec=ModelSetLoadAllUc)
        mock.return_value = return_value

        with exp as e, luna_bench._usecase_container.modelset_load_all_uc.override(mock):
            assert ModelSet.load_all() == e
            mock.assert_called_once_with()

    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            (Success(ModelSetDomain(id=1, name="a", models=[])), nullcontext(ModelSet(id=1, name="a", models=[]))),
            (Failure(UnknownLunaBenchError(exception=RuntimeError())), pytest.raises(RuntimeError)),
        ],
    )
    def test_remove_model(
        self,
        return_value: Result[ModelSetDomain, UnknownLunaBenchError],
        exp: AbstractContextManager[ModelSet | RuntimeError],
    ) -> None:
        mock: Mock = Mock(spec=ModelRemoveUc)
        mock.return_value = return_value

        ms_name = "b"
        ms = ModelSet(id=1, name=ms_name, models=[ModelMetadata(id=1, name="A", hash=1)])
        with exp as e, luna_bench._usecase_container.model_remove_uc.override(mock):
            model = simple_model("A")
            ms.remove_model(model=model)

            assert ms == e
            mock.assert_called_once_with(modelset_name=ms_name, model=model)

    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            (Success(None), nullcontext(None)),
            (Failure(UnknownLunaBenchError(exception=RuntimeError())), pytest.raises(RuntimeError)),
        ],
    )
    def test_delete(
        self, return_value: Result[None, UnknownLunaBenchError], exp: AbstractContextManager[ModelSet | RuntimeError]
    ) -> None:
        mock: Mock = Mock(spec=ModelSetDeleteUc)
        mock.return_value = return_value

        ms = ModelSet(id=1, name="b", models=[ModelMetadata(id=1, name="A", hash=1)])
        with exp, luna_bench._usecase_container.modelset_delete_uc.override(mock):
            ms.delete()

            mock.assert_called_once_with(modelset_name=ms.name)
