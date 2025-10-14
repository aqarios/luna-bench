from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext
from unittest.mock import Mock

import pytest
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import ModelMetadataDomain, ModelSetDomain
from luna_bench._internal.usecases.modelset.protocols import (
    ModelAddUc,
    ModelLoadAllUc,
    ModelRemoveUc,
    ModelSetCreateUc,
    ModelSetDeleteUc,
    ModelSetLoadAllUc,
)
from luna_bench.components import ModelMetadata, ModelSet
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.dao.data_not_unique_error import DataNotUniqueError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from tests.unit.fixtures.mock_model import _dummy_model


class TestModelData:
    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            (
                Success(ModelSetDomain(id=1, name="Test", models=[])),
                nullcontext(ModelSet(id=1, name="Test", models=[])),
            ),
            (Failure(DataNotUniqueError()), pytest.raises(RuntimeError)),
        ],
    )
    def test_create(
        self,
        return_value: Result[ModelSetDomain, DataNotUniqueError | Exception],
        exp: AbstractContextManager[ModelSet | RuntimeError],
    ) -> None:
        mock: Mock = Mock(spec=ModelSetCreateUc)
        mock.return_value = return_value

        with exp as e:
            r = ModelSet.create(modelset_name="Test", modelset_create=mock)
            mock.assert_called_with(modelset_name="Test")

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

        r = ModelSet.load_all_models(model_all=mock)
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

        with exp as e:
            model = _dummy_model("A")
            modelset.add(model=model, modelset_add=mock)
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
        mock: Mock = Mock(spec=ModelSetLoadAllUc)
        mock.return_value = return_value

        name: str = return_value.unwrap().name if is_successful(return_value) else "a"
        with exp as e:
            m = ModelSet.load(name=name, modelset_load=mock)
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

        with exp as e:
            assert ModelSet.load_all(modelset_load_all=mock) == e
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
        with exp as e:
            model = _dummy_model("A")
            ms.remove_model(model=model, modelset_remove=mock)

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
        with exp:
            ms.delete(modelset_delete_uc=mock)

            mock.assert_called_once_with(modelset_name=ms.name)
