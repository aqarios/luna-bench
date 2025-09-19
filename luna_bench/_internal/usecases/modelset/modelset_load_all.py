from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject
from returns.pipeline import is_successful
from returns.result import Failure, Result, Success

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.user_models import ModelMetadataUserModel, ModelSetUserModel
from luna_bench.errors.unknown_error import UnknownLunaBenchError

from .protocols import ModelSetLoadAllUc

if TYPE_CHECKING:
    from luna_bench._internal.domain_models import ModelSetDomain


class ModelSetLoadAllUcImpl(ModelSetLoadAllUc):
    """Implementation of the use case for loading all model sets."""

    _transaction: DaoTransaction

    @inject
    def __init__(self, transaction: DaoTransaction = Provide[DaoContainer.transaction]) -> None:
        """
        Initialize the ModelSetLoadAllUcImpl with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self._transaction = transaction

    def __call__(self) -> Result[list[ModelSetUserModel], UnknownLunaBenchError]:
        """
        Load all model sets.

        Returns
        -------
        Result[list[ModelSetDomain], UnknownLunaBenchError]
            On success: Contains the list of all model sets
            On failure: An Exception
        """
        with self._transaction as t:
            result_dao = t.modelset.load_all()
            if not is_successful(result_dao):
                return Failure(result_dao.failure())

            result_unwrapped: list[ModelSetDomain] = result_dao.unwrap()

            return Success(
                # TODO(Llewellyn): needs to be optimized. Loop in loop...# noqa: FIX002
                [
                    ModelSetUserModel(
                        id=r.id,
                        name=r.name,
                        models=[
                            ModelMetadataUserModel.model_validate_json(m.model_dump_json(exclude={"model"}))
                            for m in r.models
                        ],
                    )
                    for r in result_unwrapped
                ]
            )
