from returns.result import Result

from luna_bench._internal.entities import StorageTransaction


class ModelSetDeleteUcImpl:
    """Implementation of the use case for deleting a model set."""

    _transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        """
        Initialize the ModelSetDeleteUcImpl with a storage transaction.

        Parameters
        ----------
        transaction : StorageTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(self, modelset_id: int) -> Result[None, Exception]:
        """
        Delete a model set.

        Permanently removes the specified model set from the database.

        Parameters
        ----------
        modelset_id : int
            The ID of the model set to delete.

        Returns
        -------
        Result[None, Exception]
            On success: Nothing
            On failure: An Exception
        """
        with self._transaction as t:
            return t.modelset.delete(modelset_id=modelset_id)
