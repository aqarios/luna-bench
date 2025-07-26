from returns.result import Result

from luna_bench._internal.entities import StorageTransaction


class ModelSetDeleteUcImpl:
    transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        self.transaction = transaction

    def __call__(self, modelset_id: int) -> Result[None, Exception]:
        with self.transaction as t:
            return t.modelset.delete(modelset_id=modelset_id)
