from __future__ import annotations

from contextlib import AbstractContextManager, nullcontext
from unittest.mock import Mock, patch

import pytest
from luna_model import Model
from returns.result import Failure, Result, Success

from luna_bench._internal.usecases.modelset.protocols import ModelFetchUc
from luna_bench.components import ModelMetadata
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from tests.utils.luna_model import simple_model


class TestModelData:
    @pytest.mark.parametrize(
        ("return_value", "exp"),
        [
            (
                Success(simple_model("A")),
                nullcontext(simple_model("A")),
            ),
            (Failure(DataNotExistError()), pytest.raises(RuntimeError)),
        ],
    )
    def test_fetch_model(
        self, return_value: Result[Model, Exception], exp: AbstractContextManager[Model | RuntimeError]
    ) -> None:
        mock: Mock = Mock(spec=ModelFetchUc)
        mock.return_value = return_value
        modeldata = ModelMetadata(id=1, name="A", hash=0)

        with exp as e:
            fetched_model = modeldata._fetch_model(model_fetch=mock)
            mock.assert_called_with(model_id=modeldata.id)
            assert isinstance(e, Model)
            assert e.encode() == fetched_model.encode()

    def test_model_calls_fetch_model(self) -> None:
        mock: Mock = Mock()
        mock.return_value = "this is a test"

        modeldata = ModelMetadata(id=1, name="A", hash=0)
        with patch.object(modeldata, "_fetch_model", mock):
            assert modeldata.model == "this is a test"
            mock.assert_called_with()
