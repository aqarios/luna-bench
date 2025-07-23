from returns.result import Result

from luna_bench._internal.entities.model_set.domain_models import ModelSetDomain
from luna_bench._internal.shared.database.transactions.storage_transaction import StorageTransaction


class ModelSetCreateUcImpl:
    storage_transaction: StorageTransaction

    def __init__(self, storage_transaction: StorageTransaction) -> None:
        self.storage_transaction = storage_transaction

    def __call__(self, modelset_name: str) -> Result[ModelSetDomain, str]:
        with self.storage_transaction as t:
            return t.model_set.create_set(modelset_name=modelset_name)
