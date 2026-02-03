from typing import TYPE_CHECKING

from dependency_injector.wiring import Provide, inject

from luna_bench._internal.dao import DaoContainer, DaoTransaction
from luna_bench._internal.usecases.modelset.protocols import ModelLoadAllUc
from luna_bench.entities import ModelMetadataEntity

if TYPE_CHECKING:
    from luna_bench._internal.domain_models import ModelMetadataDomain


class ModelLoadAllUcImpl(ModelLoadAllUc):
    """Implementation of the use case for retrieving the metadata of all models."""

    transaction: DaoTransaction

    @inject
    def __init__(self, transaction: DaoTransaction = Provide[DaoContainer.transaction]) -> None:
        """
        Initialize the ModelAllUcImpl with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self.transaction = transaction

    def __call__(self) -> list[ModelMetadataEntity]:
        """
        Retrieve the metadata of all models from the dao.

        Returns
        -------
        list[ModelMetadataEntity]
            A list of all model metadata objects.
        """
        with self.transaction as t:
            domain_models: list[ModelMetadataDomain] = t.model.get_all()

            # TODO(Llewellyn): maybe there is a way to do that with a pydantic type adapter. # noqa: FIX002
            #  But not sure because of the exclude.
            return [
                ModelMetadataEntity.model_validate_json(domain_model.model_dump_json(exclude={"model"}))
                for domain_model in domain_models
            ]
