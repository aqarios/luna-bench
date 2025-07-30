from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext
from unittest.mock import Mock

import pytest
from returns.result import Failure, Result, Success

from luna_bench._internal.entities import ModelMetadataDomain, ModelSetDomain
from luna_bench._internal.usecases import ModelAllUc, ModelSetAddUc, ModelSetCreateUc
from luna_bench.components import ModelSet
from luna_bench.components.model_set import ModelData
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.storage.data_not_unique_error import DataNotUniqueError
from tests.unit.fixtures.mock_usecase import _dummy_model


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
            ([ModelMetadataDomain(id=1, name="A", hash=1)], [ModelData(id=1, model_name="A", model_hash=1)]),
            ([], []),
        ],
    )
    def test_load_all_models(self, return_value: list[ModelMetadataDomain], exp: list[ModelData]) -> None:
        mock: Mock = Mock(spec=ModelAllUc)
        mock.return_value = return_value

        r = ModelSet.load_all_models(model_all=mock)
        mock.assert_called_with()

        assert exp == r

    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            (
                Success(ModelSetDomain(id=1, name="B", models=[ModelMetadataDomain(id=1, name="A", hash=1)])),
                nullcontext(ModelSet(id=1, name="B", models=[ModelData(id=1, model_name="A", model_hash=1)])),
            ),
            (Failure(DataNotExistError()), pytest.raises(RuntimeError)),
        ],
    )
    def test_add_model(
        self, return_value: Result[ModelSetDomain, Exception], exp: AbstractContextManager[ModelSet | RuntimeError]
    ) -> None:
        mock: Mock = Mock(spec=ModelSetAddUc)
        mock.return_value = return_value
        modelset = ModelSet(id=1, name="B", models=[])

        with exp as e:
            model = _dummy_model("A")
            modelset.add(model=model, modelset_add=mock)
            mock.assert_called_with(modelset_id=1, model=model)
            assert e == modelset
