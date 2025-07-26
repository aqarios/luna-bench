from luna_bench._internal.entities import ModelMetadataDomain, StorageTransaction


class ModelAllUcImpl:
    transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        self.transaction = transaction

    def __call__(self) -> list[ModelMetadataDomain]:
        with self.transaction as t:
            return t.model.get_all()
