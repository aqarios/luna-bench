from returns.result import Result

from luna_bench._internal.dao import DaoTransaction
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class ModelSetDeleteUcImpl:
    """Implementation of the use case for deleting a model set."""

    _transaction: DaoTransaction

    def __init__(self, transaction: DaoTransaction) -> None:
        """
        Initialize the ModelSetDeleteUcImpl with a storage transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(self, modelset_name: str) -> Result[None, DataNotExistError | UnknownLunaBenchError]:
        """
        Delete a model set.

        Permanently removes the specified model set from the database.

        Parameters
        ----------
        modelset_name : str
            The name of the model set to delete.

        Returns
        -------
        Result[None, DataNotExistError | UnknownLunaBenchError]
            On success: Nothing
            On failure: An Exception
        """
        with self._transaction as t:
            return t.modelset.delete(modelset_name=modelset_name)
