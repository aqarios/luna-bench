from luna_quantum import Logging
from pydantic import BaseModel, ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models.arbitrary_data_domain import ArbitraryDataDomain
from luna_bench._internal.domain_models.registered_data_domain import RegisteredDataDomain
from luna_bench._internal.registries import PydanticRegistry
from luna_bench._internal.registries.base_registry import BaseRegistry
from luna_bench.errors.registry.unknown_component_error import UnknownComponentError
from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class ArbitraryDataRegistry[USER_MODEL: BaseModel](
    BaseRegistry[USER_MODEL], PydanticRegistry[USER_MODEL, RegisteredDataDomain]
):
    logging = Logging.get_logger(__name__)

    def from_domain_to_user_model(
        self, domain_model: RegisteredDataDomain
    ) -> Result[USER_MODEL, UnknownIdError | ValidationError]:
        result: Result[type[USER_MODEL], UnknownIdError] = self.get_by_id(domain_model.registered_id)

        if not is_successful(result):
            return Failure(result.failure())
        try:
            return Success(result.unwrap().model_validate(domain_model.data, from_attributes=True))
        except ValidationError as e:
            return Failure(e)

    def from_user_model_to_domain_model(
        self, user_model: USER_MODEL
    ) -> Result[RegisteredDataDomain, UnknownComponentError]:
        register_id: Result[str, UnknownComponentError] = self.get_by_cls(user_model.__class__)

        if not is_successful(register_id):
            return Failure(register_id.failure())
        return Success(
            RegisteredDataDomain.model_construct(
                registered_id=register_id.unwrap(),
                data=ArbitraryDataDomain.model_validate(user_model.model_dump()),
            )
        )
