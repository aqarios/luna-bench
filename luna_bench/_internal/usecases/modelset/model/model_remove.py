from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from luna_quantum import Model
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.usecases.modelset.protocols import ModelRemoveUc
from luna_bench._internal.user_models import ModelMetadataUserModel, ModelSetUserModel
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

if TYPE_CHECKING:
    from luna_bench._internal.domain_models import ModelMetadataDomain, ModelSetDomain


class ModelRemoveUcImpl(ModelRemoveUc):
    """Implementation of the use case for removing a model from a model set."""

    _transaction: DaoTransaction

    @inject
    def __init__(self, transaction: DaoTransaction = Provide[DaoContainer.transaction]) -> None:
        """
        Initialize the ModelSetRemoveUcImpl with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction

    def __call__(
        self, modelset_name: str, model: Model
    ) -> Result[ModelSetUserModel, DataNotExistError | UnknownLunaBenchError]:
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

            result_dao: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError] = t.modelset.remove_model(
                modelset_name=modelset_name, model_id=get_result.unwrap().id
            )

            if not is_successful(result_dao):
                return Failure(result_dao.failure())

            result_unwrapped: ModelSetDomain = result_dao.unwrap()
            # TODO(Llewellyn): needs to be improved maybe with type adapter or something  # noqa: FIX002
            result: ModelSetUserModel = ModelSetUserModel(
                id=result_unwrapped.id,
                name=result_unwrapped.name,
                models=[
                    ModelMetadataUserModel.model_validate_json(m.model_dump_json(exclude={"model"}))
                    for m in result_unwrapped.models
                ],
            )

            return Success(result)
