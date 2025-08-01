from luna_quantum import Model
from returns.pipeline import is_successful
from returns.result import Result, Success

from luna_bench._internal.entities import StorageTransaction
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class ModelFetchUcImpl:
    """Implementation of the use case for fetching the data of a model."""

    transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        """
        Initialize the ModelFetchUcImpl with a storage transaction.

        Parameters
        ----------
        transaction : StorageTransaction
            The transaction object used to interact with the storage.
        """
        self.transaction = transaction

    def __call__(self, model_id: int) -> Result[Model, DataNotExistError | UnknownLunaBenchError]:
        """
        Retrieve the model data from the database.

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
        with self.transaction as t:
            result = t.model.fetch_model(model_id)

            if is_successful(result):
                return Success(Model.decode(result.unwrap()))
            return result
