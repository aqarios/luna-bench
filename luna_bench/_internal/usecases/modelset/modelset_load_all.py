from returns.result import Result

from luna_bench._internal.dao import StorageTransaction
from luna_bench._internal.domain_models import ModelSetDomain
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class ModelSetLoadAllUcImpl:
    """Implementation of the use case for loading all model sets."""

    _transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        """
        Initialize the ModelSetLoadAllUcImpl with a storage transaction.

        Parameters
        ----------
        transaction : StorageTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(self) -> Result[list[ModelSetDomain], UnknownLunaBenchError]:
        """
        Load all model sets.

        Returns
        -------
        Result[list[ModelSetDomain], UnknownLunaBenchError]
            On success: Contains the list of all model sets
            On failure: An Exception
        """
        with self._transaction as t:
            return t.modelset.load_all()
