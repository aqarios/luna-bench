from luna_bench._internal.entities import ModelMetadataDomain, StorageTransaction


class ModelAllUcImpl:
    """Implementation of the use case for retrieving the metadata of all models."""

    transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        """
        Initialize the ModelAllUcImpl with a storage transaction.

        Parameters
        ----------
        transaction : StorageTransaction
            The transaction object used to interact with the storage.
        """
        self.transaction = transaction

    def __call__(self) -> list[ModelMetadataDomain]:
        """
        Retrieve the metadata of all models from the storage.

        Returns
        -------
        list[ModelMetadataDomain]
            A list of all model metadata objects.
        """
        with self.transaction as t:
            return t.model.get_all()
