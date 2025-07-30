from luna_quantum import Model
from returns.pipeline import is_successful
from returns.result import Failure, Result

from luna_bench._internal.entities import ModelMetadataDomain, ModelSetDomain, StorageTransaction


class ModelSetRemoveUcImpl:
    """Implementation of the use case for removing a model from a model set."""

    _transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        """
        Initialize the ModelSetRemoveUcImpl with a storage transaction.

        Parameters
        ----------
        transaction : StorageTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(self, modelset_id: int, model: Model) -> Result[ModelSetDomain, Exception]:
        """
        Remove a model from a model set.

        Retrieves the model metadata using the model hash and removes it from the specified model set.

        Parameters
        ----------
        modelset_id : int
            The ID of the model set to remove the model from.
        model : Model
            The model to remove from the model set.

        Returns
        -------
        Result[ModelSetDomain, Exception]
            On success: Contains the updated model set object
            On failure: An Exception
        """
        with self._transaction as t:
            get_result: Result[ModelMetadataDomain, Exception] = t.model.get(model_hash=model.__hash__())

            if not is_successful(get_result):
                return Failure(get_result.failure())

            result: Result[ModelSetDomain, Exception] = t.modelset.remove_model(
                modelset_id=modelset_id, model_id=get_result.unwrap().id
            )
            return result
