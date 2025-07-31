from typing import TYPE_CHECKING

import pytest
from returns.result import Success

from luna_bench._internal.usecases.models.protocols import ModelFetchUc
from luna_bench._internal.usecases.usecase_container import UsecaseContainer
from tests.unit.fixtures.mock_usecase import _dummy_model

if TYPE_CHECKING:
    from luna_bench._internal.usecases import ModelAllUc


class TestModelUc:
    def test_model_all(self, usecase: UsecaseContainer) -> None:
        uc: ModelAllUc = usecase.model_all_uc()
        assert len(uc()) == 2

    @pytest.mark.parametrize(
        ("modelset_name", "exp"),
        [
            (1, Success(_dummy_model())),
            (3, Success(ModelSetDomain(id=2, name="MS2", models=[]))),
        ],
    )
    def test_create(
            self,
            usecase: UsecaseContainer,
            modelset_name: str,
            exp: Result[ModelSetDomain, DataNotUniqueError | UnknownLunaBenchError],
    ) -> None:
    def test_model_fetch(self, usecase: UsecaseContainer) -> None:
        uc: ModelFetchUc = usecase.model_fetch_uc()
