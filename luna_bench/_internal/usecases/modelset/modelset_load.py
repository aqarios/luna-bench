from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench.entities import ModelMetadataEntity, ModelSetEntity
from luna_bench.errors.dao.data_not_exist_error import DataNotExistError
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import ModelSetLoadUc

if TYPE_CHECKING:
    from luna_bench._internal.domain_models import ModelSetDomain


class ModelSetLoadUcImpl(ModelSetLoadUc):
    """Implementation of the use case for loading a specific model set."""

    _transaction: DaoTransaction

    @inject
    def __init__(self, transaction: DaoTransaction = Provide[DaoContainer.transaction]) -> None:
        """
        Initialize the ModelSetLoadUcImpl with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction

    def __call__(self, modelset_name: str) -> Result[ModelSetEntity, DataNotExistError | UnknownLunaBenchError]:
        """
        Load a specific model set.

        Parameters
        ----------
        modelset_name : str
            The name of the model set to load.

        Returns
        -------
        Result[ModelSetEntity, DataNotExistError | UnknownLunaBenchError]
            On success: Contains the model set object
            On failure: An Exception
        """
        with self._transaction as t:
            result_dao: Result[ModelSetDomain, DataNotExistError | UnknownLunaBenchError] = t.modelset.load(
                modelset_name=modelset_name
            )
            if not is_successful(result_dao):
                return Failure(result_dao.failure())

            result_unwrapped: ModelSetDomain = result_dao.unwrap()
            # TODO(Llewellyn): needs to be improved maybe with type adapter or something # noqa: FIX002
            result: ModelSetEntity = ModelSetEntity(
                id=result_unwrapped.id,
                name=result_unwrapped.name,
                models=[
                    ModelMetadataEntity.model_validate_json(m.model_dump_json(exclude={"model"}))
                    for m in result_unwrapped.models
                ],
            )

            return Success(result)
