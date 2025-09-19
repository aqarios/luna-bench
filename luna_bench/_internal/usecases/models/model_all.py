from luna_bench._internal.dao import DaoTransaction
from luna_bench._internal.domain_models import ModelMetadataDomain


class ModelAllUcImpl:
    """Implementation of the use case for retrieving the metadata of all models."""

    transaction: DaoTransaction

    def __init__(self, transaction: DaoTransaction) -> None:
        """
        Initialize the ModelAllUcImpl with a dao transaction.

        Parameters
        ----------
        transaction : DaoTransaction
            The transaction object used to interact with the dao.
        """
        self.transaction = transaction

    def __call__(self) -> list[ModelMetadataDomain]:
        """
        Retrieve the metadata of all models from the dao.

        Returns
        -------
        list[ModelMetadataDomain]
            A list of all model metadata objects.
        """
        with self.transaction as t:
            return t.model.get_all()
