from abc import abstractmethod
from typing import Protocol, TypeVar

from pydantic import BaseModel, ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result

from luna_bench._internal.domain_models.base_domain import BaseDomain
from luna_bench.errors.registry.unknown_id_error import UnknownIdError

DomainModel_contra = TypeVar("DomainModel_contra", bound=BaseDomain, contravariant=True)
UserModel_co = TypeVar("UserModel_co", bound=BaseModel, covariant=True)


class Mapper(Protocol[DomainModel_contra, UserModel_co]):
    @abstractmethod
    def to_user_model(self, domain: DomainModel_contra) -> Result[UserModel_co, UnknownIdError | ValidationError]: ...

    def return_to_user_model[E](
        self,
        result: Result[DomainModel_contra, E],
    ) -> Result[UserModel_co, E | UnknownIdError | ValidationError]:
        if not is_successful(result):
            return Failure(result.failure())
        domain = result.unwrap()
        return self.to_user_model(domain)


class ListMapper(Mapper[DomainModel_contra, UserModel_co]):
    @abstractmethod
    def to_user_model_list(
        self,
        domain_models: list[DomainModel_contra],
    ) -> Result[list[UserModel_co], UnknownIdError | ValidationError]: ...
