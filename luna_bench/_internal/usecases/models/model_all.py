from returns.result import Result

from luna_bench._internal.entities.model_set.domain_models import ModelMetadataDomain
from luna_bench._internal.shared.database.transactions.storage_transaction import StorageTransaction
from luna_bench.errors.modeset.model_already_exists_error import ModelAlreadyExistsError


class ModelAllUcImpl:
    storage_transaction: StorageTransaction

    def __init__(self, storage_transaction: StorageTransaction) -> None:
        self.storage_transaction = storage_transaction

    def __call__(self) -> Result[list[ModelMetadataDomain], str]:
        with self.storage_transaction as t:
            result: Result[list[ModelMetadataDomain], ModelAlreadyExistsError | str] = t.model_set.get_all_models()

            return result
