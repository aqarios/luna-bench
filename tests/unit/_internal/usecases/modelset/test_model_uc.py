from typing import TYPE_CHECKING

import pytest
from luna_quantum import Model
from returns.result import Failure, Result, Success

from luna_bench._internal.usecases.usecase_container import UsecaseContainer
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError
from tests.unit.fixtures.mock_model import _dummy_model

if TYPE_CHECKING:
    from luna_bench._internal.usecases import ModelLoadAllUc
    from luna_bench._internal.usecases.modelset.protocols import ModelFetchUc


class TestModelUc:
    def test_model_all(self, usecase: UsecaseContainer) -> None:
        uc: ModelLoadAllUc = usecase.model_load_all_uc()
        assert len(uc()) == 2

    @pytest.mark.parametrize(
        ("model_id", "exp"),
        [
            (1, Success(_dummy_model("M1"))),
            (3, Failure(DataNotExistError())),
        ],
    )
    def test_model_fetch(
        self, usecase: UsecaseContainer, model_id: int, exp: Result[Model, DataNotExistError | UnknownLunaBenchError]
    ) -> None:
        uc: ModelFetchUc = usecase.model_fetch_uc()
        result: Result[Model, DataNotExistError | UnknownLunaBenchError] = uc(model_id=model_id)
        assert type(result) is type(exp)
        if isinstance(exp, Success):
            assert result.unwrap().encode() == exp.unwrap().encode()
        else:
            assert isinstance(result.failure(), type(exp.failure()))
