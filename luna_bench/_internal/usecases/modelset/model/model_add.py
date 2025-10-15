from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from luna_quantum import Model
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.usecases.modelset.protocols import ModelAddUc
from luna_bench._internal.user_models import ModelSetUserModel
from luna_bench._internal.user_models.model_metadata_usermodel import ModelMetadataUserModel
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

if TYPE_CHECKING:
    from luna_bench._internal.domain_models import ModelMetadataDomain, ModelSetDomain


class ModelAddUcImpl(ModelAddUc):
    """Implementation of the use case for adding a model to a model set."""

    _transaction: DaoTransaction

    @inject
    def __init__(self, transaction: DaoTransaction = Provide[DaoContainer.transaction]) -> None:
        """
        Initialize the ModelSetAddUcImpl with a dao transaction.

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
        Add a model to a model set.

        Creates or retrieves the model metadata and adds it to the specified model set.

        Parameters
        ----------
        modelset_name : str
            The ID of the model set to add the model to.
        model : Model
            The model to add to the model set.

        Returns
        -------
        Result[ModelSetDomain, UnknownLunaBenchError]
            On success: Contains the updated model set object
            On failure: An Exception
        """
        with self._transaction as t:
            result_create: Result[ModelMetadataDomain, UnknownLunaBenchError] = t.model.get_or_create(
                model_name=model.name, model_hash=model.__hash__(), binary=model.encode()
            )
            if not is_successful(result_create):
                return Failure(result_create.failure())
            success_create: ModelMetadataDomain = result_create.unwrap()

            result_add: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError] = t.modelset.add_model(
                modelset_name=modelset_name,
                model_id=success_create.id,
            )
            if not is_successful(result_add):
                return Failure(result_add.failure())
            r: ModelSetDomain = result_add.unwrap()
            # TODO(Llewellyn): needs to be improved maybe with type adapter or something  # noqa: FIX002
            result: ModelSetUserModel = ModelSetUserModel(
                id=r.id,
                name=r.name,
                models=[
                    ModelMetadataUserModel.model_validate_json(m.model_dump_json(exclude={"model"})) for m in r.models
                ],
            )

            return Success(result)
