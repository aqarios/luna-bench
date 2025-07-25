from luna_quantum import Model
from returns.pipeline import is_successful
from returns.result import Result

from luna_bench._internal.entities import ModelMetadataDomain, ModelSetDomain, StorageTransaction
from luna_bench.errors.modeset.model_already_exists_error import ModelAlreadyExistsError


class ModelSetAddUcImpl:
    transaction: StorageTransaction

    def __init__(self, transaction: StorageTransaction) -> None:
        self.transaction = transaction

    def __call__(self, dataset_id: int, model: Model) -> Result[ModelSetDomain, str]:
        with self.transaction as t:
            result_create: Result[ModelMetadataDomain, ModelAlreadyExistsError | str] = t.model.get_or_create(
                model_name=model.name, model_hash=model.__hash__(), binary=model.encode()
            )
            if not is_successful(result_create):
                return result_create
            success_create: ModelMetadataDomain = result_create.unwrap()

            result_add: Result[ModelSetDomain, str] = t.modelset.add_model(
                modelset_id=dataset_id,
                model_id=success_create.id,
            )
            return result_add
