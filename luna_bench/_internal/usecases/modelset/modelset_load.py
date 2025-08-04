from returns.result import Result

from luna_bench._internal.entities import ModelSetDomain, StorageTransaction
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class ModelSetLoadUcImpl:
    """Implementation of the use case for loading a specific model set."""

    _transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        """
        Initialize the ModelSetLoadUcImpl with a storage transaction.

        Parameters
        ----------
        transaction : StorageTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(self, modelset_name: str) -> Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]:
        """
        Load a specific model set.

        Parameters
        ----------
        modelset_name : str
            The name of the model set to load.

        Returns
        -------
        Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]
            On success: Contains the model set object
            On failure: An Exception
        """
        with self._transaction as t:
            return t.modelset.load(modelset_name=modelset_name)
