from returns.result import Result

from luna_bench._internal.shared.database.transactions.storage_transaction import StorageTransaction


class ModelSetDeleteUcImpl:
    storage_transaction: StorageTransaction

    def __init__(self, storage_transaction: StorageTransaction) -> None:
        self.storage_transaction = storage_transaction

    def __call__(self, modelset_id: int) -> Result[None, str]:
        with self.storage_transaction as t:
            return t.model_set.delete_modelset(modelset_id=modelset_id)
