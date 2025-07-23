from luna_quantum import Model
from returns.pipeline import is_successful
from returns.result import Result

from luna_bench._internal.entities.model_set.domain_models import ModelMetadataDomain, ModelSetDomain
from luna_bench._internal.shared.database.transactions.storage_transaction import StorageTransaction


class ModelSetRemoveUcImpl:
    storage_transaction: StorageTransaction

    def __init__(self, storage_transaction: StorageTransaction) -> None:
        self.storage_transaction = storage_transaction

    def __call__(self, dataset_id: int, model: Model) -> Result[ModelSetDomain, str]:
        with self.storage_transaction as t:
            get_result: Result[ModelMetadataDomain, str] = t.model_set.get_model(model_hash=model.__hash__())

            if not is_successful(get_result):
                return get_result

            result: Result[ModelMetadataDomain, str] = t.model_set.remove_model_from_modelset(
                modelset_id=dataset_id, model_id=get_result.unwrap().id
            )
            return result
