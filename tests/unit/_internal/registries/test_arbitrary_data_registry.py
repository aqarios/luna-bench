import pytest
from pydantic import BaseModel, ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.registered_data_domain import RegisteredDataDomain
from luna_bench._internal.registries.arbitrary_data_registry import ArbitraryDataRegistry
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class TestArbitraryDataRegistry:
    class StrictModel(BaseModel):
        a_string: str
        model_config = {"extra": "forbid"}

    @pytest.fixture()
    def demo_registry(self) -> ArbitraryDataRegistry[BaseModel]:
        r = ArbitraryDataRegistry[BaseModel]("demo")
        r.register("registered", TestArbitraryDataRegistry.StrictModel)
        return r

    @pytest.mark.parametrize(
        ("domain_model", "exp"),
        [
            (
                RegisteredDataDomain(
                    registered_id="registered",
                    data=ArbitraryDataDomain.model_validate({"a_string": "test"}, from_attributes=True),
                ),
                Success(StrictModel(a_string="test")),
            ),
            (
                RegisteredDataDomain(
                    registered_id="not_registered",
                    data=ArbitraryDataDomain.model_validate({"a_string": "test"}, from_attributes=True),
                ),
                Failure(UnknownIdError("demo", "not_registered")),
            ),
            (
                RegisteredDataDomain(
                    registered_id="registered",
                    data=ArbitraryDataDomain.model_validate({"xD": "xD"}, from_attributes=True),
                ),
                Failure(ValidationError.from_exception_data(title="", line_errors=[])),
            ),
        ],
    )
    def test_from_domain_to_user_model(
        self,
        demo_registry: ArbitraryDataRegistry[BaseModel],
        domain_model: RegisteredDataDomain,
        exp: Result[BaseModel, UnknownIdError | ValidationError],
    ) -> None:
        result = demo_registry.from_domain_to_user_model(domain_model)

        assert type(result) is type(exp)

        if is_successful(result):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))

    @pytest.mark.parametrize(
        ("user_model", "exp"),
        [
            (
                StrictModel(
                    a_string="test",
                ),
                Success(
                    RegisteredDataDomain(
                        registered_id="registered",
                        data=ArbitraryDataDomain.model_validate({"a_string": "test"}, from_attributes=True),
                    )
                ),
            ),
            (
                ArbitraryDataDomain(),
                Failure(UnknownComponentError("demo", BaseModel)),
            ),
        ],
    )
    def test_from_user_model_to_domain_model(
        self,
        demo_registry: ArbitraryDataRegistry[BaseModel],
        user_model: BaseModel,
        exp: Result[BaseModel, UnknownComponentError],
    ) -> None:
        result = demo_registry.from_user_model_to_domain_model(user_model)

        assert type(result) is type(exp)

        if is_successful(result):
            assert result.unwrap() == exp.unwrap()
        else:
            assert isinstance(result.failure(), type(exp.failure()))
