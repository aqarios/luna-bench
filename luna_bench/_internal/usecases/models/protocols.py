from typing import Protocol

from luna_quantum import Model
from returns.result import Result

from luna_bench._internal.domain_models import ModelMetadataDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class ModelAllUc(Protocol):
    """Protocol for retrieving all models."""

    def __call__(self) -> list[ModelMetadataDomain]:
        """
        Retrieve all models from storage.

        Returns
        -------
        list[ModelMetadataDomain]
            A list of all model metadata domain objects.
        """
        ...


class ModelFetchUc(Protocol):
    """Protocol for retrieving model data from the database."""

    def __call__(self, model_id: int) -> Result[Model, DataNotExistError | UnknownLunaBenchError]:
        """
        Retrieve model data from the database.

        Parameters
        ----------
        model_id : int
            The id of the model to fetch.

        Returns
        -------
        Result[Model, DataNotExistError | UnknownLunaBenchError]
            On Success: The model data fetched from the database.
            On Failure: An error.
        """
        ...
