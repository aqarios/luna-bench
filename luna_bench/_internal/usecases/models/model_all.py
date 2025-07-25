from returns.result import Result

from luna_bench._internal.entities import ModelMetadataDomain, StorageTransaction
from luna_bench.errors.modeset.model_already_exists_error import ModelAlreadyExistsError


class ModelAllUcImpl:
    transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        self.transaction = transaction

    def __call__(self) -> Result[list[ModelMetadataDomain], str]:
        with self.transaction as t:
            result: Result[list[ModelMetadataDomain], ModelAlreadyExistsError | str] = t.model.get_all()

            return result
