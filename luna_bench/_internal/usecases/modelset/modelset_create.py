from returns.result import Result

from luna_bench._internal.entities import ModelSetDomain, StorageTransaction


class ModelSetCreateUcImpl:
    """Implementation of the use case for creating a model set."""

    _transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        """
        Initialize the ModelSetCreateUcImpl with a storage transaction.

        Parameters
        ----------
        transaction : StorageTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(self, modelset_name: str) -> Result[ModelSetDomain, Exception]:
        """
        Create a new model set with the given name.

        Parameters
        ----------
        modelset_name : str
            The name of the model set to create.

        Returns
        -------
        Result[ModelSetDomain, Exception]
            On success: Contains the created model set object
            On failure: An Exception
        """
        with self._transaction as t:
            return t.modelset.create(name=modelset_name)
