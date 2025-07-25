from returns.result import Result

from luna_bench._internal.entities import ModelSetDomain, StorageTransaction


class ModelSetCreateUcImpl:
    transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        self.transaction = transaction

    def __call__(self, modelset_name: str) -> Result[ModelSetDomain, str]:
        with self.transaction as t:
            return t.modelset.create(name=modelset_name)
