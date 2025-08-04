from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext
from unittest.mock import Mock, patch

import pytest
from luna_quantum import Model
from returns.result import Failure, Result, Success

from luna_bench._internal.usecases.models.protocols import ModelFetchUc
from luna_bench.components.model_set import ModelData
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from tests.unit.fixtures.mock_usecase import _dummy_model


class TestModelData:
    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            (
                Success(_dummy_model("A")),
                nullcontext(_dummy_model("A")),
            ),
            (Failure(DataNotExistError()), pytest.raises(RuntimeError)),
        ],
    )
    def test_fetch_model(
        self, return_value: Result[Model, Exception], exp: AbstractContextManager[Model | RuntimeError]
    ) -> None:
        mock: Mock = Mock(spec=ModelFetchUc)
        mock.return_value = return_value
        modeldata = ModelData(id=1, model_name="A", model_hash=0)

        with exp as e:
            fetched_model = modeldata._fetch_model(model_fetch=mock)
            mock.assert_called_with(model_id=modeldata.id)
            assert isinstance(e, Model)
            assert e.encode() == fetched_model.encode()

    def test_model_calls_fetch_model(self) -> None:
        mock: Mock = Mock()
        mock.return_value = "this is a test"

        modeldata = ModelData(id=1, model_name="A", model_hash=0)
        with patch.object(modeldata, "_fetch_model", mock):
            assert modeldata.model == "this is a test"
            mock.assert_called_with()
