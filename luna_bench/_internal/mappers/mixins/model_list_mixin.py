from pydantic import ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.mappers.types import DomainModel_contra, ListMapper, UserModel_co
from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class ModelListMixin(ListMapper[DomainModel_contra, UserModel_co]):
    def to_user_model_list(
        self,
        domain_models: list[DomainModel_contra],
    ) -> Result[list[UserModel_co], UnknownIdError | ValidationError]:
        """
        Convert a list of domain models to a list of user models.

        Parameters
        ----------
        domain_models: list[DomainModel]
            The list of domain models to convert.

        Returns
        -------
        Result[list[UserModel], UnknownIdError | ValidationError]
            Successful conversion: The list of user models. Otherwise, an exception.
        """
        results: list[UserModel_co] = []
        for domain_model in domain_models:
            result: Result[UserModel_co, UnknownIdError | ValidationError] = self.to_user_model(domain_model)
            if not is_successful(result):
                return Failure(result.failure())
            results.append(result.unwrap())
        return Success(results)
