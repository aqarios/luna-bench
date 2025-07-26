from luna_quantum import Model
from returns.pipeline import is_successful
from returns.result import Failure, Result

from luna_bench._internal.entities import ModelMetadataDomain, ModelSetDomain, StorageTransaction


class ModelSetAddUcImpl:
    """Implementation of the use case for adding a model to a model set."""

    _transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        """
        Initialize the ModelSetAddUcImpl with a storage transaction.

        Parameters
        ----------
        transaction : StorageTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(self, dataset_id: int, model: Model) -> Result[ModelSetDomain, Exception]:
        """
        Add a model to a model set.

        Creates or retrieves the model metadata and adds it to the specified model set.

        Parameters
        ----------
        dataset_id : int
            The ID of the model set to add the model to.
        model : Model
            The model to add to the model set.

        Returns
        -------
        Result[ModelSetDomain, Exception]
            On success: Contains the updated model set object
            On failure: An Exception
        """
        with self._transaction as t:
            result_create: Result[ModelMetadataDomain, Exception] = t.model.get_or_create(
                model_name=model.name, model_hash=model.__hash__(), binary=model.encode()
            )
            if not is_successful(result_create):
                return Failure(result_create.failure())
            success_create: ModelMetadataDomain = result_create.unwrap()

            result_add: Result[ModelSetDomain, Exception] = t.modelset.add_model(
                modelset_id=dataset_id,
                model_id=success_create.id,
            )
            return result_add
