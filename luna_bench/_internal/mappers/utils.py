from collections.abc import Callable

from pydantic import BaseModel, ValidationError
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.domain_models import RegisteredDataDomain
from luna_bench._internal.registries import PydanticRegistry
from luna_bench.errors.registry.unknown_id_error import UnknownIdError


class MapperUtils:
    @staticmethod
    def to_user_model_list[D, U, I: BaseModel](
        domain_models: list[D],
        registry: PydanticRegistry[I, RegisteredDataDomain],
        converter: Callable[
            [D, PydanticRegistry[I, RegisteredDataDomain]], Result[U, UnknownIdError | ValidationError]
        ],
    ) -> Result[list[U], UnknownIdError | ValidationError]:
        """
        Convert a list of domain models to a list of user models.

        Parameters
        ----------
        domain_models: list[D]
            The list of domain models to convert.
        registry: PydanticRegistry[I, RegisteredDataDomain]
            Pydantic registry to use for the conversion.
        converter: Callable[[D, PydanticRegistry[I, RegisteredDataDomain]], Result[U, UnknownIdError | ValidationError]]
            Domain model to user model converter.

        Returns
        -------
        Result[list[U], UnknownIdError | ValidationError]
            Successful conversion: The list of user models. Otherwise, an exception.
        """
        results: list[U] = []
        for domain_model in domain_models:
            result: Result[U, UnknownIdError | ValidationError] = converter(domain_model, registry)
            if not is_successful(result):
                return Failure(result.failure())
            results.append(result.unwrap())
        return Success(results)
