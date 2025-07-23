from luna_quantum import Model
from returns.pipeline import is_successful
from returns.result import Result

from luna_bench._internal.entities.model_set.domain_models import ModelMetadataDomain, ModelSetDomain
from luna_bench._internal.shared.database.transactions.storage_transaction import StorageTransaction
from luna_bench.errors.modeset.model_already_exists_error import ModelAlreadyExistsError


class ModelSetAddUcImpl:
    storage_transaction: StorageTransaction

    def __init__(self, storage_transaction: StorageTransaction) -> None:
        self.storage_transaction = storage_transaction

    def __call__(self, dataset_id: int, model: Model) -> Result[ModelSetDomain, str]:
        with self.storage_transaction as t:
            result_create: Result[ModelMetadataDomain, ModelAlreadyExistsError | str] = t.model_set.get_or_create_model(
                model_name=model.name, model_hash=model.__hash__(), binary=model.encode()
            )
            if not is_successful(result_create):
                return result_create
            success_create: ModelMetadataDomain = result_create.unwrap()

            result_add: Result[ModelSetDomain, str] = t.model_set.add_model_to_modelset(
                modelset_id=dataset_id,
                model_id=success_create.id,
            )
            return result_add
