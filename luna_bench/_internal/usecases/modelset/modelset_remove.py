from luna_quantum import Model
from returns.pipeline import is_successful
from returns.result import Failure, Result

from luna_bench._internal.dao import DaoTransaction
from luna_bench._internal.domain_models import ModelMetadataDomain, ModelSetDomain
from luna_bench.errors.storage.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError


class ModelSetRemoveUcImpl:
    """Implementation of the use case for removing a model from a model set."""

    _transaction: DaoTransaction

    def __init__(self, transaction: DaoTransaction) -> None:
        """
        Initialize the ModelSetRemoveUcImpl with a storage transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the storage.
        """
        self._transaction = transaction

    def __call__(
        self, modelset_name: str, model: Model
    ) -> Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]:
        """
        Remove a model from a model set.

        Retrieves the model metadata using the model hash and removes it from the specified model set.

        Parameters
        ----------
        modelset_name : str
            The ID of the model set to remove the model from.
        model : Model
            The model to remove from the model set.

        Returns
        -------
        Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError]
            On success: Contains the updated model set object
            On failure: An Exception
        """
        with self._transaction as t:
            get_result: Result[ModelMetadataDomain, DataNotExistError | UnknownLunaBenchError] = t.model.get(
                model_hash=model.__hash__()
            )

            if not is_successful(get_result):
                return Failure(get_result.failure())

            result: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError] = t.modelset.remove_model(
                modelset_name=modelset_name, model_id=get_result.unwrap().id
            )
            return result
