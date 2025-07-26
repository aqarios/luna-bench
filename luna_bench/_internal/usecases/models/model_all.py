from returns.result import Result

from luna_bench._internal.entities import ModelMetadataDomain, StorageTransaction


class ModelAllUcImpl:
    transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        self.transaction = transaction

    def __call__(self) -> Result[list[ModelMetadataDomain], Exception]:
        with self.transaction as t:
            result: Result[list[ModelMetadataDomain], Exception] = t.model.get_all()

            return result
